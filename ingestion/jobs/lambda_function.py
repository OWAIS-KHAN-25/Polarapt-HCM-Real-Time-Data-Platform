"""USAJOBS API -> S3. Reference reconstruction; verify against deployed Lambda before claiming code parity."""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
import boto3

s3 = boto3.client('s3')

def lambda_handler(event, context):
    params = urllib.parse.urlencode({'ResultsPerPage': 500, 'Page': 1})
    url = 'https://data.usajobs.gov/api/search?' + params
    req = urllib.request.Request(url, headers={
        'Host': 'data.usajobs.gov',
        'User-Agent': os.environ['USAJOBS_EMAIL'],
        'Authorization-Key': os.environ['USAJOBS_API_KEY'],
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        status = resp.status
        source_data = json.loads(resp.read().decode('utf-8'))
    records = source_data.get('SearchResult', {}).get('SearchResultItems', [])
    if not isinstance(records, list):
        raise ValueError('Unexpected USAJOBS SearchResultItems response')
    now = datetime.now(timezone.utc)
    metadata = {'source': 'jobs', 'timestamp': now.isoformat(), 'record_count': len(records), 'response_status': status}
    payload = {'metadata': metadata, 'data': records}
    key = f'raw/jobs/{now:%Y/%m/%d/%H%M}.json'
    s3.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=key,
                  Body=json.dumps(payload, default=str).encode('utf-8'),
                  ContentType='application/json',
                  Metadata={k: str(v) for k, v in metadata.items()})
    return {'statusCode': 200, 'body': json.dumps({'records': len(records), 's3_key': key})}
