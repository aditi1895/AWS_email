from flask import Flask, render_template, request
from botocore.config import Config
from werkzeug.utils import secure_filename
from constants import *
import boto3
import uuid

app = Flask(__name__)

@app.route('/', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home_page():
    if 'user' not in request.form.keys():
        return "Provide a username"
    elif 'pass' not in request.form.keys():
        return 'Invalid Password!'
    key = {'User':{'S':str(request.form['user'])}}
    response = scan_dynamodb_table(key)
    item = response['Item']
    password = item['Password']['S']

    if password == request.form['pass']:
        return render_template('form_to_upload.html')
    else:
        return "Invalid Username or Password!"

@app.route('/uploader', methods=['POST'])
def upload_file():
    if 'Emails' not in request.form.keys() or len(request.form['Emails']) == 0:
        return 'No Email Addresses provided!'

    email_string = request.form['Emails']
    emails = request.form['Emails'].strip().split(',')
    if len(emails)>4:
        return "Max of 4 email addresses are allowed"

    if 'file' not in request.files:
        return "No File uploaded"

    file_handler = request.files['file']
    file_handler_filename = secure_filename(file_handler.filename)
    resp_s3 = upload_file_to_s3_bucket(file_handler, file_handler_filename)
    print('resp_s3', resp_s3)
    if resp_s3:
        item = create_dynamodb_item(resp_s3, email_string)
        resp = update_dynamodb_table(item)
        print("table update successfully with the response {}".format(resp))
    return "File saved successfully!"

def boto_client(resource):
    retry_config = Config(retries=dict(max_attempts=6), region_name=AWS_REGION)
    if resource=='dynamodb':
        client = boto3.client(resource, config=retry_config, aws_access_key_id= AWS_ACCESS_KEY, aws_secret_access_key= AWS_SECRET_KEY)
    else:
        client = boto3.client(resource, aws_access_key_id= AWS_ACCESS_KEY, aws_secret_access_key= AWS_SECRET_KEY)
    return client

def upload_file_to_s3_bucket(file, filename):
    try:
        client = boto_client("s3")
        client.upload_fileobj(
            file,
            BUCKET,
            filename,
            ExtraArgs = {
                "ContentType": file.content_type
            }
        )

        return filename
    except Exception as e:
        print("uploading file object to s3 failed {}".format(e))
        return e
    
def create_dynamodb_item(filename, emails):
    filepath = 'https://s3.us-east-2.amazonaws.com/'+BUCKET+'/'+filename
    Item={'primary_key': {'S': str(uuid.uuid4())}, 'Filename' : {'S': filepath}, 
                'Emails': {'S': emails}, 'Clicked_on_file': {'SS': [""]}}
    return Item

def update_dynamodb_table(item):
    try:
        client = boto_client('dynamodb')
        resp = client.put_item(TableName=TABLE, Item=item)
        return resp
    except Exception as e:
        print("updating dynamodb table failed {}".format(e))

def scan_dynamodb_table(key):
    client = boto_client('dynamodb')
    response = client.get_item(TableName=TABLE_LOGIN, Key=key)
    print('get response {}'.format(response))
    return response

if __name__ == '__main__':
    app.run(debug=True)