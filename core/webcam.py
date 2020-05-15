from flask import Flask, jsonify, request, redirect, make_response
import logging, sys, time
import cv2
import numpy as np
import os, re
from werkzeug.datastructures import ImmutableMultiDict
import face_recognition
import json
from google.cloud import firestore
from datetime import date

# Intializion code. Also reduces cold start time 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)


# This functions checks for image file extensions 
# curl -XPOST -F "file=@harsh.jpeg "  -F 'data={"url":"","time":"20","email":""}' http://localhost:5000/upload 
def allowed_file(filename):
    """
    params:
        - filename: Name of the image to be checked for extension 
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    This path takes two inputs in multiform/data.
    Name of paramaters:
    file: Image of the user
    url: Url of the video
    email: To add date to database
    time: Number of seconds to look for that person. Max: 5mins, can be configured to 15mins on cloud run 
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            return make_response(jsonify("Msg: Upload an image"),415)


        data= json.loads(request.form["data"])
        if data["time"]:
            if type(int(data["time"]))!=type(3):
                return make_response(jsonify("Msg: Time should be an integer"))
            if int(data["time"])>300:
                return make_response(jsonify("Msg: Time cannot be more than 300 seconds"))
        test_url = re.search("^http|https|rstp", data["url"])
        if test_url:
            file = request.files['file']

            if file.filename == '':
                return make_response(jsonify("Msg: Upload an image"),415)

            if file and allowed_file(file.filename):
                found = detect_faces(file,data)
                if found:
                    datetoDB(data["email"])
                    return make_response(jsonify("Msg: Person Found"),200)
                else:
                    return make_response(jsonify("Msg: Person not found"),417)
        else:
            return make_response(jsonify("Msg: Invalid url"), 415)

# Adds dates to DB in form of a list
def datetoDB(email):
    db = firestore.Client()
    doc_ref = db.collection(u'users').document(email)

    today = date.today().strftime("%d/%m/%Y")
    doc_ref.set({u'date': str(today) }, merge=True)
    logger.info("Date added")    


@app.route('/compare', methods=['POST'])
def compare():
    """
    This path takes two inputs in multiform/data
    Name of paramaters:
    image1: First image
    image2 : Second image
    """
    if request.method == 'POST':
        if 'image1' not in request.files or 'image2' not in request.files:
            return make_response(jsonify("Msg: Upload an image"),415)

        image1 = request.files['image1']
        image2 = request.files['image2']
        if image1.filename == '' or image2.filename == '':
            return make_response(jsonify("Msg: Upload an image"),415)

        if image1 and allowed_file(image1.filename):
            if image2 and allowed_file(image2.filename):
                load_image1 = face_recognition.load_image_file(image1)
                load_image2 = face_recognition.load_image_file(image2)

                face1_encoding = face_recognition.face_encodings(load_image1)[0]
                face2_encoding = face_recognition.face_encodings(load_image2)[0]

                face_distances = face_recognition.face_distance([face1_encoding], face2_encoding)
                complement = 1 - face_distances
                percent = complement*100
                msg = "The faces are "+str(percent)+ " percent alike"
                return make_response(jsonify(msg), 200)
            else:
                return make_response(jsonify("Msg:upload an image"),415)
        else:
            return make_response(jsonify("Msg:upload an image"),415)
    else: 
            return make_response(jsonify("Invalid request ", 403))


@app.route('/check', methods=['POST'])
def check():
    """
    This function checks the number of faces in an image 
    Name of paramaters:
    image: First image
    """
    if request.method == 'POST':
        logger.debug("Post request")
        if 'image' not in request.files :
            logger.debug("No file or wrong parameter name")
            return make_response(jsonify("Msg: Upload an image"),415)

        image = request.files['image']
        if image.filename == '' :
            logger.debug("No file  ")
            return make_response(jsonify("Msg: Upload an image"),415)

        if image and allowed_file(image.filename):
            load_image = face_recognition.load_image_file(image)
            face_no = face_recognition.face_locations(load_image)

            if len(face_no)>1:
                return make_response(jsonify("Please upload a pic with only one person in it"), 415)
            
            return make_response(jsonify("Great! Pic has only one person in it"), 200)

   
# Detects a face, returns boolean
def detect_faces(file_stream, data):

    """
    params:
    - file_stream: Image served as binary stream
    - data: Url for video source
    """
    logger.debug("Into detect faces function")
    start_time = time.perf_counter()
    logger.info(data['url'])
    for i in range(5):
        try: 
            video_capture = cv2.VideoCapture(data['url']) 
        except:
            if i > 5:
                return False
            else:
                logger.debug("retrying to fetch the video")
              
    try:
        logger.debug("Loading image file")
        person_tobe_found = face_recognition.load_image_file(file_stream)
        person_tbf_encoding = face_recognition.face_encodings(person_tobe_found)[0]

        known_face_encodings = [
            person_tbf_encoding
        ]
        known_face_names = [
            data["email"]
        ]

        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
    except:
        e = sys.exc_info()
        logger.exception(e)
        return False


    while True:
        try:
            logger.debug("Read the video feed")
            ret, frame = video_capture.read()
            small_frame = cv2.resize(frame,None, fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            if process_this_frame:
                logger.debug("Processing a frame")
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance= 0.5)
                    name = "Unknown"

                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]                   
                    
                    face_names.append(name)
                    logger.debug(face_names)
                    if data["email"] in face_names:
                        logger.info("Actually found the person")
                        return True
        except:
            e = sys.exc_info()
            logger.exception(e)
        process_this_frame = not process_this_frame

        end_time = time.perf_counter()
        run_time = end_time - start_time
        look_time = int(data["time"])
        if run_time > look_time: # No. of seconds we look for that person 
            return False

    video_capture.release()
    cv2.destroyAllWindows()
