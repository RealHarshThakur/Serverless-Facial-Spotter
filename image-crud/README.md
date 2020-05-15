# image-crud

This folder contains the code necessary for image operations on Google Cloud Storage. 
Service is deployed on Cloud Run. I have created the container image using Cloud Native Buildpacks

- pack build gcr.io/steady-service-269616/gcs-image:latest --builder=cloudfoundry/cnb:tiny --publish
