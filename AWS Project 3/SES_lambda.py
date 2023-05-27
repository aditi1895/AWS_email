from email import message
import boto3
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def lambda_handler(event, context):
    try:
        event = json.loads(event)
    except:
        event = event
    
    print("event {}".format(event))
    record = event["Records"][0]
    if record['eventName'] == "INSERT":
        data = extract_data(record)
        print("data",data)
        responses, errors = send_emails(data, "mani.accesswork@gmail.com")
        if len(responses)== len(data['Emails']):
            print("All emails {} sent successfully".format(data['Emails']))
        elif len(errors)>0:
            print("Error in sending the emails {}".format(errors))

def extract_data(record):
    record_data = {}
    try:
        db_record = record['dynamodb']
        record_data['Emails'] = db_record['NewImage']['Email Addresses']['SS']
        record_data['Filepath'] = db_record['NewImage']['File']['S']
        record_data['Accessed'] = db_record['NewImage']['Accessed_By']['SS']
        record_data['partition_key'] = db_record['NewImage']['partition_key']['S']
        return record_data
        
    except Exception as e:
        print("Error {} in extracting data".format(e))
        return e

def send_emails(data, sender):
    email_client = boto3.client("ses")
    responses, errors = [], []
    for email in data['Emails']:
        try:
            message = create_email_template(email, data)

            message['From'] = sender
            print('message {}'.format(message.as_string()))
            response = email_client.send_raw_email(           
                        Source= sender,
                        Destinations = [email],
                        RawMessage = {
                            'Data': message.as_string()
                        },
                        ConfigurationSetName = "notification_on_click"
                    )
            responses.append(response)
        except Exception as e:
            errors.append(e)
            print("Error {} with SES client".format(e))
    return responses, errors

def create_email_template(email,data):
    
    message = MIMEMultipart('mixed')
    message['partition_key'] = data['partition_key']
    message['To'] = email
    message['Subject'] = "Admin has shared a new file!"
    BODY_HTML = '<html><head></head><body><h1>Hello!</h1><p> Admin has uploaded a new file. Open it to look for contents. </p> '

    BODY_HTML+='<br> <a href="'
    BODY_HTML+=data['Filepath']
    BODY_HTML+='">Click on FILE</a>'
    BODY_HTML+= '<br> Have a Good day! <br> Thanks </body></html> '
    
    CHARSET = "utf-8"
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    message_body = MIMEMultipart('alternative')
    message_body.attach(htmlpart)

    message.attach(message_body)
    return message