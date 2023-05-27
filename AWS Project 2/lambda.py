from http import client
import json
from pydoc import cli
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def lambda_handler(event, context):
    try:
        event = json.loads(event)
    except TypeError:
        event = event

    print("event {}".format(event))
    record = event['Records'][0]
    if 'eventSource' in record.keys():
        eventResource = record['eventSource']
    elif 'EventSource' in record.keys():
        eventResource = record['EventSource']

    if "dynamodb" in eventResource:
        if record['eventName'] == "INSERT":
            data = extract_data_dynamodb(event)
            print("data",data)
            responses, errors = email_sender(data, "tutorpointcase1@gmail.com")
            if len(responses)== len(data['emails']):
                print("All emails sent successfully")
            elif len(errors)>0:
                print("Error in sending the emails {}".format(errors))
    
    elif "sns" in eventResource:
        print('sns')
        message = json.loads(event['Records'][0]['Sns']['Message'])
        if message['eventType'] == 'Click':
            data = extract_data_sns(message)
            Key = {'primary_key':{'S':str(data['primary_key'])}}
            items = scan_dynamodb_table(Key)
            print('items1 {}'.format(items))
            clicked = items['Item']['Clicked_on_file']['SS']
            if data['destination'] not in clicked:
                if clicked[0] == "":
                    clicked = [data['destination']]
                else:
                    clicked.append(data['destination'])
            item = items['Item']
            item['Clicked_on_file']['SS'] = clicked
            resp = update_dynamodb_table(item)
            emails = items['Item']['Emails']['S'].strip().split(',')
            
            print('clicked {}, emails {}'.format(item['Clicked_on_file']['SS'], emails))
            if len(clicked) == len(emails):
                filename = item['Filename']['S']
                print('deleting object')
                resp = delete_object(filename)

def boto_client(resource):
    client = boto3.client(resource)
    return client

def SESclient():
    return boto3.client("ses")

def extract_data_dynamodb(event):
    data = {}
    try:
        images = event['Records'][0]['dynamodb']
        data['emails'] = images['NewImage']['Emails']['S'].strip().split(',')
        data['filepath'] = images['NewImage']['Filename']['S']
        data['primary_key'] = images['NewImage']['primary_key']['S']
        data['clicked'] = images['NewImage']['Clicked_on_file']['SS']
        return data
    except Exception as e:
        print("error in reading event for dynamodb")
    

def email_sender(data, sender):
    print('data {}, sender {}'.format(data, sender))
    ses_client = SESclient()
    responses, errors = [], []
    try:
        for email in data['emails']:
            message = MIMEMultipart('mixed')
            message['Subject'] = "Click on the uploaded file!"
            message['From'] = sender 
            message['To'] = email
            BODY_TEXT = "Hello,\r\nHope you are doing well! Admin has uploaded a file, please click on it to check the contents."
            BODY_HTML = '<html><head></head><body><h1>Hello!</h1><p>Hope you are doing well! <br> Admin has uploaded a file, please click on it to check the contents..</p> '

            BODY_HTML+='<br> <a href="'
            BODY_HTML+=data['filepath']
            BODY_HTML+='">FILE</a>'
            BODY_HTML+= '<br> Thanks </body></html> '
            
            CHARSET = "utf-8"
            message_body = MIMEMultipart('alternative')

            textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
            htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
            message_body.attach(textpart)
            message_body.attach(htmlpart)
            
            message.attach(message_body)
            message['X-SES-CONFIGURATION-SET'] = "notifyclick"
            message['primary_key'] = data['primary_key']
            message.add_header('X-SES-CONFIGURATION-SET', "notifyclick")
            print('message {}'.format(message.as_string()))
            email_client = SESclient()
            response = email_client.send_raw_email(           
                        Source= sender,
                        Destinations = [email],
                        RawMessage = {
                            'Data': message.as_string()
                        },
                        ConfigurationSetName = "notifyclick"
                    )
            responses.append(response)
    except Exception as e:
        errors.append(e)
    return responses, errors

def extract_data_sns(message):
    data = {}
    try:
        Email = message['mail']
        data['destination'] = Email['destination'][0]            
        data['headers'] = Email['headers']
        for keys in data['headers']:
            if keys['name'] == 'primary_key':
                data['primary_key'] = keys['value']
        return data
    except Exception as e:
        return e


def scan_dynamodb_table(key):
    client = boto_client('dynamodb')
    response = client.get_item(TableName='shivabanoth-table', Key=key)
    print('get response {}'.format(response))
    return response

def update_dynamodb_table(item):
    try:
        client = boto_client('dynamodb')
        resp = client.put_item(TableName='shivabanoth-table', Item=item)
        return resp
    except Exception as e:
        print("updating dynamodb table failed {}".format(e))

def delete_object(filename):
    try:
        client = boto_client('s3')
        bucket, key = filename.strip().split('/')[-2], filename.strip().split('/')[-1]
        response = client.delete_object(
        Bucket=bucket,
        Key=key
    )
        return response
    except Exception as e:
        print("deleting object from s3 failed {}".format(e))