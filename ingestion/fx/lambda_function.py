"""Open Exchange Rates -> S3 (working approach)."""
import json
import os
import urllib.request
import urllib.error
import boto3
from datetime import datetime, timezone

s3 = boto3.client('s3')
CURRENCIES = ['PKR', 'SAR', 'AED', 'GBP', 'EUR', 'INR']

def lambda_handler(event, context):
    app_id = os.environ['OPENEXCHANGE_APP_ID']
    bucket = os.environ['S3_BUCKET_NAME']
    url = 'https://openexchangerates.org/api/latest.json?app_id=' + app_id
    request = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
            api_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Open Exchange Rates API HTTP error: {error.code}') from None
    rates = api_data.get('rates', {})
    missing = [currency for currency in CURRENCIES if currency not in rates]
    if missing:
        raise ValueError(f'Missing currencies: {missing}')
    if api_data.get('base') != 'USD':
        raise ValueError('Expected USD as base currency')
    now = datetime.now(timezone.utc)
    metadata = {'source': 'open_exchange_rates', 'timestamp': now.isoformat(),
                'record_count': len(CURRENCIES), 'response_status': status}
    payload = {'metadata': metadata, 'base_currency': api_data['base'],
               'api_timestamp': api_data.get('timestamp'),
               'rates': {currency: rates[currency] for currency in CURRENCIES}}
    key = f'raw/fx/{now:%Y/%m/%d/%H%M}.json'
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(payload, indent=2).encode('utf-8'),
                  ContentType='application/json',
                  Metadata={k: str(v) for k, v in metadata.items()})
    return {'statusCode': 200, 'body': json.dumps({'message': 'FX rates uploaded successfully',
                                                  'records': len(CURRENCIES), 's3_key': key})}
