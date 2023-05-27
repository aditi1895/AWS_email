import boto3
import uuid
from werkzeug.utils import secure_filename
from constants import *
from botocore.config import Config

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def update_table(filepath, emails):
    try:
        print('filepath',filepath)
        retry_config = Config(retries=dict(max_attempts=6), region_name=AWS_REGION)
        dynamodb = boto3.client('dynamodb', config= retry_config, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        resp = dynamodb.put_item(TableName='FileInfo', Item={'User': {'S': str(uuid.uuid4())}, 'Source file' : {'S': filepath}, 
                'Emails': {'S': emails}, 'Clicked': {'SS': [""]}})
        return resp
    except Exception as e:
        print("Something Happened while updating Dynamodb table: ", e)
        return e
    


def upload_file_to_s3(file):
    filename = secure_filename(file.filename)
    try:
        s3.upload_fileobj(
            file,
            AWS_BUCKET_NAME,
            filename,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened while uploading file to s3: ", e)
        return e

    # after upload file to s3 bucket, return filename of the uploaded file
    return file.filename