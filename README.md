# Serverless-Facial-Spotter
Facial spotter built entirely on serverless stack. 


# Objective
After a user creates a profile on the website, they can provide a video source link which could even be a livestream(CCTV,etc) and the app responds whether the person is found. To extend it to be an attendance system, when the user is found, there will be an entry in the database on which dates user is found. 

# Components involved

- Frontend is backed by Vercel Now. 
- Backend is backed by Cloud Run.
- Images are stored on Google Cloud Storage
- Firestore is used for storing dates and bucket names associated with the profile


# Additional features
- Compare how similar two faces are. 
