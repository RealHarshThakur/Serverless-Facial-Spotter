# The logic responsible for recognising people

This is deployed on Google Cloud Run service. 

# Reason to avoid AWS Lambda
  Lambda has deployment package limits set to 250mb. The machine learning models are over 120mb and fetching it from S3 each time function goes cold led to slow cold starts. 
