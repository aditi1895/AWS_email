import boto3
from botocore.config import Config
from gevent import config

class SESClient(object):

    _ses_client = None

    @staticmethod
    def get_ses_client():
        retry_config = Config(retries=dict(max_attempts=6))
        if not SESClient._ses_client:
            SESClient._ses_client = boto3.client('ses', config=retry_config)
        return SESClient._ses_client