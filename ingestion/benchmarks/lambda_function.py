"""O*NET selected occupation salary benchmark scraper -> S3 (working approach)."""
import os
import json
import re
import boto3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

s3 = boto3.client('s3')
OCCUPATIONS = {
    'Software Developers': '15-1252.00',
    'Physicians, Pathologists': '29-1222.00',
    'Dentists, General': '29-1021.00',
    'Physicians, Anesthesiologists': '29-1211.00',
    'Physicians, Dermatologists': '29-1215.00',
    'Physicians, Cardiologists': '29-1212.00',
    'Physicians, Neurologists': '29-1217.00',
    'Physicians, Radiologists': '29-1224.00',
    'Orthodontists': '29-1023.00',
    'Oral and Maxillofacial Surgeons': '29-1022.00'
}

def lambda_handler(event, context):
    results = []
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    for name, code in OCCUPATIONS.items():
        url = f'https://www.onetonline.org/link/summary/{code}'
        response = session.get(url, timeout=3)
        response.raise_for_status()
        text = BeautifulSoup(response.text, 'html.parser').get_text(' ', strip=True)
        match = re.search(r'Median wages\s*\((\d{4})\).*?\$([\d,]+)\s+annual', text, re.IGNORECASE)
        if not match:
            raise ValueError(f'Salary missing: {name}')
        results.append({'occupation': name, 'onet_code': code,
                        'salary_year': int(match.group(1)),
                        'median_annual_salary_usd': int(match.group(2).replace(',', '')),
                        'source_url': url})
    if len(results) != 10:
        raise ValueError('Expected exactly 10 occupations')
    results.sort(key=lambda row: row['median_annual_salary_usd'], reverse=True)
    now = datetime.now(timezone.utc)
    metadata = {'source': 'onet_occupational_wages', 'timestamp': now.isoformat(),
                'record_count': len(results), 'response_status': 200,
                'ranking_scope': '10_selected_occupations', 'currency': 'USD'}
    key = f'raw/benchmarks/{now:%Y/%m/%d/%H%M}.json'
    s3.put_object(Bucket=os.environ['S3_BUCKET_NAME'], Key=key,
                  Body=json.dumps({'metadata': metadata, 'data': results}, indent=2).encode('utf-8'),
                  ContentType='application/json',
                  Metadata={k: str(metadata[k]) for k in ('source','timestamp','record_count','response_status')})
    return {'statusCode': 200, 'body': json.dumps({'message': 'Benchmarks uploaded successfully',
                                                  'records': len(results), 's3_key': key})}
