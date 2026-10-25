"""SNS Standard -> S3 object metadata -> SNS FIFO. Reference implementation, NOT DEPLOYED."""
import json
import os
import urllib.parse
import boto3

s3 = boto3.client('s3')
sns = boto3.client('sns')
SOURCE_TO_ROUTE = {'jobs': 'jobs', 'onet_occupational_wages': 'benchmarks',
                   'benchmarks': 'benchmarks', 'open_exchange_rates': 'fx', 'fx': 'fx'}

def lambda_handler(event, context):
    count = 0
    for notification in event.get('Records', []):
        envelope = json.loads(notification['Sns']['Message'])
        for record in envelope.get('Records', []):
            if not record.get('eventName', '').startswith('ObjectCreated:'):
                continue
            bucket = record['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(record['s3']['object']['key'])
            if not key.startswith('raw/') or not key.endswith('.json'):
                continue
            head = s3.head_object(Bucket=bucket, Key=key)
            contract = head.get('Metadata', {})
            source = SOURCE_TO_ROUTE.get(contract.get('source'))
            if source is None:
                raise ValueError(f'Unknown source for object {key}')
            # Stable dedup ID for a single object version/event. FIFO dedup window ~5 minutes.
            sequencer = record['s3']['object'].get('sequencer', '')
            event_id = f'{bucket}/{key}/{sequencer}'
            import hashlib
            dedup_id = hashlib.sha256(event_id.encode()).hexdigest()
            message = {'source': source, 'bucket': bucket, 'key': key,
                       'record_count': contract.get('record_count'),
                       'timestamp': contract.get('timestamp'),
                       'response_status': contract.get('response_status')}
            sns.publish(TopicArn=os.environ['ROUTED_TOPIC_ARN'],
                        Message=json.dumps(message),
                        MessageGroupId=source,
                        MessageDeduplicationId=dedup_id,
                        MessageAttributes={'source': {'DataType': 'String', 'StringValue': source}})
            count += 1
    return {'statusCode': 200, 'routed': count}
