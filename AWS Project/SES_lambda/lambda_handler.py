import json
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def lambda_handler(event, context):
    try:
        event_conv = json.loads(event)
    except TypeError:
        event_conv = event
    print("validating event recieved {}".format(event))
    records = is_valid_event(event_conv)
    events = records[0]['dynamodb']
    emails = events['NewImage']['Emails']['S'].strip().split(',')
    filepath = events['NewImage']['Source file']['S']
    user = events['NewImage']['User']['S']
    # loveygarg15@gmail.com'
    resp = send_email(emails,filepath, 'tutorpointdevice3@gmail.com', user)
    print('resp {} filepath {}'.format(resp, filepath))

def is_valid_event(event_dict):
    try:
        records = event_dict['Records']
        return records
    except:
        return "Not a valid S3 object {}".format(event_dict)

def send_email(emails,filepath, sender, user):
    responses = []
    for email in emails:
        print('email {}'.format(email))
        msg = MIMEMultipart('mixed')
        msg['Subject'] = "A file has been uploaded"
        msg['From'] = sender 
        msg['To'] = email
        BODY_TEXT = "Hello,\r\nPlease see the attached file for a list of customers to contact."
        BODY_HTML = '<html><head></head><body><h1>Hello!</h1><p>Please find the link to the uploaded file here.</p> '

        BODY_HTML+='<br> <a href="'
        BODY_HTML+=filepath
        BODY_HTML+='">FILE</a>'
        BODY_HTML+= '<br> Thanks </body></html> '
        
        CHARSET = "utf-8"
        msg_body = MIMEMultipart('alternative')

        textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
        htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

# Add the text and HTML parts to the child container.
        msg_body.attach(textpart)
        msg_body.attach(htmlpart)
        
        msg.attach(msg_body)
        msg['X-SES-CONFIGURATION-SET'] = "emailclicknotification"
        msg['User'] = user
        msg.add_header('X-SES-CONFIGURATION-SET', "emailclicknotification")
        print('message {}'.format(msg.as_string()))
        email_client = SESclient()
        response = email_client.send_raw_email(
                    
                    Source= sender,
                    Destinations = [email],
                    RawMessage = {
                        'Data': msg.as_string()
                    },
                    ConfigurationSetName = "emailclicknotification"
                )
        responses.append(response)
    return responses

def SESclient():
    ses_client = None
    # retry_config = Config(retries=dict(max_attempts=6))
    if not ses_client:
        ses_client = boto3.client('ses')
    return ses_client