import boto3, os
import json

TABLE = os.environ['Table']

def lambda_handler(event, context):
    try:
        event = json.loads(event)
    except:
        event = event

    record = event['Records'][0]
    sns_message = json.loads(record['Sns']['Message'])
    if sns_message['eventType'] == 'Click':
        sns_data = extract_data(sns_message)
        items = get_item_from_db({'partition_key': {'S': sns_data['partition_key']}}, TABLE)
        item = items['Item']
        accessed = item['Accessed_By']['SS']
        if sns_data['destination_email'] not in accessed:
            if accessed[0] == "":
                accessed = [sns_data['destination_email']]
            else:
                accessed.append(sns_data['destination_email'])
        print('updating')
        resp = update_item_in_db({'partition_key': {'S': sns_data['partition_key']}}, {"Accessed_By": {"Action": "PUT",  "Value": {"SS":accessed}}} ,TABLE)
        print('update resp', resp)
        Emails = item['Email Addresses']['SS']
        print("Emsils and accessed ", Emails, accessed, len(set(Emails) & set(accessed)))
        if len(set(Emails) & set(accessed)) == len(Emails):
            print('delete_object')
            repsonse_s3 = delete_object_from_s3(item['File']['S'])
            print('resp', repsonse_s3)
            if repsonse_s3:
                print("File Deleted Successfully!")

def extract_data(sns_message):
    data = {}
    try:
        Email = sns_message['mail']
        data['headers'] = Email['headers']
        for keys in data['headers']:
            if keys['name'] == 'partition_key':
                data['partition_key'] = keys['value']
        data['destination_email'] = Email['destination'][0] 

        return data
    except Exception as e:
        return e

def boto3_client(resource):
    # config = Config(retries=dict(max_attempts=3), region_name=AWS_REGION)
    client = boto3.client(resource)#, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key= AWS_SECRET_KEY)
    return client

def update_item_in_db(key, update, table):
    try:
        client = boto3_client('dynamodb')
        response = client.update_item(TableName=table, Key=key, AttributeUpdates=update, ReturnValues="UPDATED_NEW")
        return response
    except Exception as e:
        print("Error {} in Updating items {} in table {} with key {}".format(e, update, table, key))
    pass

def get_item_from_db(key, table):
    try:
        client = boto3_client('dynamodb')
        response = client.get_item(TableName=table, Key=key)
        return response
    except Exception as e:
        print("Error {} in getting items from table {} with key {}".format(e, table, key))
    
def delete_object_from_s3(filename):
    try:
        client = boto3_client('s3')
        print("filename", filename)
        bucket, filename = filename.strip().split('/')[-2], filename.strip().split('/')[-1]
        print("bucket", bucket, filename)
        respone = client.delete_object(
        Bucket=bucket,
        Key=filename
    )
        return respone
    except Exception as e:
        print("Error {} in deleting object from bucket {} with filename {}".format(e, bucket, filename))
