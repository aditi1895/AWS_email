import json
import boto3

def lambda_handler(event, context):
    print('event {}'.format(event))
    record = event['Records'][0]['Sns']['Message']
    message = json.loads(record)
    if 'eventType' in message:
        event = message['eventType']
        if event == 'Click':
            mail = message['mail']
            print('mail {}'.format(mail))
            dest = mail['destination'][0]
            headers = mail['headers']
            for dicts in headers:
                if dicts['name'] == 'User':
                    user = dicts['value']
            table = boto3.client('dynamodb')
            items = get_from_table(table, user)
            item = items['Item']
            print('find clicked and emails {}'.format(item))
            print('add destination to clicked then add to table')
            # add_to_table()
            clicked = item['Clicked']['SS']
            sourcefile = item['Source file']['S']
            emails = item['Emails']['S'].strip().split(',')
            if dest not in clicked:
                clicked.append(dest)
            item['Clicked']['SS'] = clicked
            print(item)
            resp = add_to_table(table, item)
            print('Item added {}'.format(item))
            print(clicked, emails)
            if len(clicked)-1 == len(emails):
                print('deleting object')
                s3 = s3_client()
                delete_object(sourcefile)
                
            
def s3_client():
    s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIA6HKHMU3HNZCX5RML",
    aws_secret_access_key="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"
    )
    return s3
    
def delete_object(filepath):
    s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIA6HKHMU3HNZCX5RML",
    aws_secret_access_key="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"
    )
    bucket, key = filepath.strip().split('/')[-2], filepath.strip().split('/')[-1]
    response = s3.delete_object(
    Bucket=bucket,
    Key=key
)
    print('delete object response {}'.format(response))
    return response

def get_from_table(table, user):
    response = table.get_item(TableName='FileInfo', Key={'User':{'S':str(user)}})
    print('get response {}'.format(response))
    return response

def add_to_table(table, item):
    response = table.put_item(TableName='FileInfo', Item = item)
    print('add response {}'.format(response))
    return response
    