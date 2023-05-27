

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

import urllib
from email_server import SESClient
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        event_conv = json.loads(event)
    except TypeError:
        event_conv = event
    # LOG.info("validating event recieved")
    records = is_valid_event(event_conv)
    events = records[0]
    for files in events:
        print("Event {}".format(files))
        filepath = files['dynamodb']
        resp = send_email(filepath)
        print('resp {} filepath {}'.format(resp, filepath))


def send_email(filepath):
    # bucket = event['Records'][0]['s3']['bucket']['name']
    # key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    email_client = SESClient.get_ses_client()

    sender = os.environ.get('SOURCE_ID', "")

    CHARSET = "utf-8"
    msg = MIMEMultipart('mixed')
    msg['Subject'] = "File Uploaded Notification"
    Message = "A File got updated in S3, please find the link, filepath {}".format(filepath)
    msg['from'] = sender

    Emails = "".strip().split(',')

    msg_body = MIMEMultipart('alternative')
    textpart = MIMEText(Message.encode(CHARSET), 'plain', CHARSET)
    msg_body.attach(textpart)

    html_body = """ <html> <head> </head> <body style="background-color:#ffff"> Hello, """ + str(Message) + """ Thanks, Kaushik </body> </html>"""
    html = MIMEText(html_body.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(html)
    msg.attach(msg_body)

    responses = []
    errors = []
    for email in Emails:
        try:
            msg['To'] = email.strip()
            response = email_client.send_raw_email(
                Source= sender,
                Destinations = [email],
                Rawmessage = {
                    'Data': msg.as_string()
                }
            )

            responses.append(response)
            print(response)
        except ClientError as exception:
            errors.append('Error {}'.format(exception))
        except Exception as ex:
            errors.append('Exception {}'.format(ex))
        
    if len(errors)>0:
        raise Exception
        


def is_valid_event(event_dict):
    event_valid = False
    valid_event_dict = {}
    try:
        records = event_dict['Records'][0]['s3']['bucket']['name']
        return records
    except:
        return "Not a valid S3 object {}".format(event_dict)