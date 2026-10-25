"""SQS benchmarks queue -> processed S3. Reference code; configure SQS trigger after testing."""
import json
import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client('s3')

def lambda_handler(event, context):
    failures = []
    for message in event.get('Records', []):
        try:
            payload = json.loads(message['body'])
            # SNS-to-SQS subscriptions default to envelope wrapping unless raw delivery enabled.
            if 'Message' in payload:
                payload = json.loads(payload['Message'])
            if payload.get('source') != 'benchmarks':
                raise ValueError('Unexpected source')
            raw = s3.get_object(Bucket=payload['bucket'], Key=payload['key'])
            data = json.loads(raw['Body'].read())
            transformed = []
            for index, item in enumerate(sorted(data['data'],
                     key=lambda x: x['median_annual_salary_usd'], reverse=True), start=1):
                transformed.append({'rank_within_selected_sample': index,
                                    'occupation': item['occupation'],
                                    'onet_code': item['onet_code'],
                                    'salary_year': item['salary_year'],
                                    'median_annual_salary_usd': item['median_annual_salary_usd']})
            output = {'metadata': {'source': 'benchmarks', 'processed_at': datetime.now(timezone.utc).isoformat(),
                                   'record_count': len(transformed), 'ranking_scope': '10_selected_occupations'},
                      'data': transformed}
            key = payload['key'].replace('raw/benchmarks/', 'processed/benchmarks/', 1)
            s3.put_object(Bucket=payload['bucket'], Key=key,
                          Body=json.dumps(output).encode('utf-8'), ContentType='application/json')
        except Exception:
            failures.append({'itemIdentifier': message['messageId']})
    return {'batchItemFailures': failures}
