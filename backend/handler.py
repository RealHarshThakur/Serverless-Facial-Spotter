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
from boto.s3.connection import S3Connection

s3_client = boto3.client('s3')
buck_name=''
response1=''
def lambda_handler(event, context):
    namee=bucket_name(buck_name)
    noImages=countObject()
    response1 = s3_client.create_bucket(
    ACL='public',
    Bucket=namee,
    CreateBucketConfiguration={
        'LocationConstraint': 'ap-south-1'
    })

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        upload_path=''.join(namee)
        s3_client.upload_file(upload_path,bucket, key)


    def bucket_name(user_input):
        N = 7
        res = ''.join(random.choices(string.ascii_uppercase + string.digits, k = N)) 
        newName = user_input+str(res)
        return newName 
    
    def countObject():
        conn = S3Connection('access-key','secret-access-key')
        bucket = conn.get_bucket('bucket')
        for key in bucket.list():
            if (key.name)[-3] == "png":
                return False

    response = {
        "statusCode": 200,
        "body": json.dumps(response1)
        }
    return response
