from utils.constansts import *
import boto3
from botocore.config import Config
from werkzeug.utils import secure_filename
import uuid, re
from flask import flash

def validate_email(email):
    # email_pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # if re.match(email_pattern, email):
    if re.fullmatch(email_pattern, email):
        return True
    else:
        return False

def boto3_client(resource):
    config = Config(retries=dict(max_attempts=3), region_name=AWS_REGION)
    client = boto3.client(resource, config=config, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key= AWS_SECRET_KEY)
    return client

def get_item_from_db(key, table):
    try:
        client = boto3_client('dynamodb')
        response = client.get_item(TableName=table, Key=key)
        return response
    except Exception as e:
        print("Error {} in getting items from table {} with key {}".format(e, table, key))
        # flash("Error {} in getting items from table {} with key {}".format(e, table, key))

def put_item_in_db(key, table):
    try:
        client = boto3_client('dynamodb')
        response = client.put_item(TableName=table, Item=key)
        return response
    except Exception as e:
        print("Error {} in Updating table {} with item {}".format(e, table, key))
        # flash("Error {} in updating table {} with item {}".format(e, table, key))

def create_item_payload(Emails, uploaded_filename):
    filepath = 'https://s3.us-east-2.amazonaws.com/'+S3_BUCKET+'/'+uploaded_filename
    Item={'partition_key': {'S': "Mani"+str(uuid.uuid4())}, 'File' : {'S': filepath},
                'Email Addresses': {'SS': Emails}, 'Accessed_By': {'SS': ['']}}
    return Item

def put_object_in_s3(Uploaded_file):
    filename = secure_filename(Uploaded_file.filename)
    try:
        client = boto3.client("s3", aws_access_key_id= AWS_ACCESS_KEY, aws_secret_access_key= AWS_SECRET_KEY)
        client.upload_fileobj(
            Uploaded_file,
            S3_BUCKET,
            filename,
            ExtraArgs = {
                "ContentType": Uploaded_file.content_type
            }
        )

        return filename
    except Exception as e:
        print("Error {} in uploading file object to s3 bucket {}".format(e, S3_BUCKET))
        # flash(("Error {} in uploading file object to s3 bucket {}".format(e, S3_BUCKET)))
        return e