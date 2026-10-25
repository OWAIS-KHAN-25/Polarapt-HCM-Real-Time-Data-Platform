"""SQS fx queue -> SQL Server via pyodbc. Reference code; NOT DEPLOYED.

Requires pyodbc and a compatible ODBC Driver 18 layer/container, networking to SQL Server,
Secrets Manager or protected environment variables, and SQS partial batch failure enabled.
"""
import json
import os
import boto3
import pyodbc
from datetime import datetime, timezone

s3 = boto3.client('s3')

def connect():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        f'SERVER={os.environ["SQLSERVER_HOST"]};'
        f'DATABASE={os.environ["SQLSERVER_DATABASE"]};'
        f'UID={os.environ["SQLSERVER_USER"]};'
        f'PWD={os.environ["SQLSERVER_PASSWORD"]};'
        'Encrypt=yes;TrustServerCertificate=no;', timeout=15)

def lambda_handler(event, context):
    failures = []
    for record in event.get('Records', []):
        try:
            msg = json.loads(record['body'])
            if 'Message' in msg:
                msg = json.loads(msg['Message'])
            if msg.get('source') != 'fx':
                raise ValueError('Wrong source')
            source = json.loads(s3.get_object(Bucket=msg['bucket'], Key=msg['key'])['Body'].read())
            ts = datetime.fromtimestamp(source['api_timestamp'], timezone.utc).replace(tzinfo=None)
            with connect() as conn:
                cur = conn.cursor()
                for currency, rate in source['rates'].items():
                    # Idempotent upsert by API timestamp and currency
                    cur.execute("""MERGE dbo.FxRates AS t
                        USING (SELECT ? AS api_timestamp, ? AS currency) AS s
                        ON t.api_timestamp=s.api_timestamp AND t.currency=s.currency
                        WHEN MATCHED THEN UPDATE SET rate=?, s3_key=?
                        WHEN NOT MATCHED THEN INSERT (api_timestamp,currency,rate,s3_key)
                        VALUES (?,?,?,?);""",
                        ts, currency, rate, msg['key'], ts, currency, rate, msg['key'])
                conn.commit()
        except Exception:
            failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': failures}
