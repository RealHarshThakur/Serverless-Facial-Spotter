from flask import Flask, jsonify, request, redirect, make_response
import logging, sys, time
import cv2
import numpy as np
import boto3
import os
import errno

sys.path.insert(0, '/tmp/') # Or any path you desire

import boto3
import os

s3_client = boto3.client('s3')

def download_dir(prefix, local, bucket, client=s3_client):
    print("downloading")
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents
    - client: initialized s3 client object
    """
    keys = []
    dirs = []
    next_token = ''
    base_kwargs = {
        'Bucket':bucket,
        'Prefix':prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != '':
            kwargs.update({'ContinuationToken': next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get('Contents')
        for i in contents:
            k = i.get('Key')
            if k[-1] != '/':
                keys.append(k)
            else:
                dirs.append(k)
        next_token = results.get('NextContinuationToken')
    for d in dirs:
        dest_pathname = os.path.join(local, d)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
    for k in keys:
        dest_pathname = os.path.join(local, k)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        client.download_file(bucket, k, dest_pathname)
        print("downloaded")

download_dir('face_recognition_models','/tmp','face-recognition-models-serverlessapi')


try:
    import face_recognition
    print("imported")
except:
    print("Retrying downloading models")
    download_dir('face_recognition_models','/tmp','face-recognition-models-serverlessapi')




ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# curl -XPOST -F "file=@ " http://127.0.0.1:5000
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            return make_response(jsonify("Msg: Upload an image"),415)

        file = request.files['file']

        if file.filename == '':
            return make_response(jsonify("Msg: Upload an image"),415)

        if file and allowed_file(file.filename):
            found = detect_faces(file)
            if found:
                return make_response(jsonify("Msg: Person Found"),200)
            else:
                return make_response(jsonify("Msg: Person not found"),417)





def detect_faces(file_stream):

    print("Into detect faces function")
    start_time = time.perf_counter()

    for i in range(3):
        try: 
            video_capture = cv2.VideoCapture('https://test-vid-12345.s3.amazonaws.com/test.webm')
        except:
            print("retrying to fetch the video")
            continue  



    try:
        print("Loading image file")
        person_tobe_found = face_recognition.load_image_file(file_stream)
        person_tbf_encoding = face_recognition.face_encodings(person_tobe_found)[0]

        known_face_encodings = [
            person_tbf_encoding
        ]
        known_face_names = [
            "Person"
        ]

        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
    except: 
        return make_response(jsonify("Msg: No face found"))


    while True:
        print("Read the video feed")
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame,None, fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if process_this_frame:
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
                logging.debug(face_names)
                if 'Person' in face_names:
                    print("Actually found the person")
                    return True

        process_this_frame = not process_this_frame

        end_time = time.perf_counter()
        run_time = end_time - start_time
        
        if run_time > 20: # No. of seconds we look for that person 
            return False

    video_capture.release()
    cv2.destroyAllWindows()