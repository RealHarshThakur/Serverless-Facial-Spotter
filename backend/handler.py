import json
import boto3
import os
import sys
import uuid
from urllib.parse import unquote_plus
from PIL import Image
import PIL.Image
import random
import string

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    buck_name=''
    namee=bucket_name(buck_name)
    
    response = s3_client.create_bucket(
    ACL='public',
    Bucket={namee},
    CreateBucketConfiguration={
        'LocationConstraint': 'ap-south-1'
    })

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        upload_path=''
        s3_client.upload_file(upload_path,bucket, key)


def bucket_name(Throw_user_input):
    N = 7
    res = ''.join(random.choices(string.ascii_uppercase + string.digits, k = N)) 
    newName = Throw_user_input+str(res)
    return newName 

    response = {
        "statusCode": 200,
        "body": json.dumps(res)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """