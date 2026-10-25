"""Reference AWS Glue Python Shell job: SQS jobs -> S3 -> Snowflake. NOT DEPLOYED.

For production, use Glue Connections/Secrets Manager and stage-and-COPY for scale.
This script uses the Snowflake Python connector; package via Glue --additional-python-modules.
Do not run concurrently without a queue-consumer ownership strategy.
"""
import json
import os
import boto3
import snowflake.connector

sqs = boto3.client('sqs')
s3 = boto3.client('s3')
QUEUE_URL = os.environ['JOBS_QUEUE_URL']

def parse_job(item):
    desc = item.get('MatchedObjectDescriptor', {})
    details = desc.get('PositionRemuneration') or []
    first = details[0] if details else {}
    return (str(desc.get('PositionID', '')),
            desc.get('PositionTitle'), desc.get('OrganizationName'),
            desc.get('PositionURI'), first.get('MinimumRange'), first.get('MaximumRange'))

def main():
    conn = snowflake.connector.connect(account=os.environ['SNOWFLAKE_ACCOUNT'],
        user=os.environ['SNOWFLAKE_USER'], password=os.environ['SNOWFLAKE_PASSWORD'],
        warehouse=os.environ['SNOWFLAKE_WAREHOUSE'], database=os.environ['SNOWFLAKE_DATABASE'],
        schema=os.environ.get('SNOWFLAKE_SCHEMA','PUBLIC'))
    try:
        for _ in range(10):
            batch = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10,
                                        WaitTimeSeconds=5, VisibilityTimeout=300).get('Messages', [])
            if not batch:
                break
            for msg in batch:
                try:
                    event = json.loads(msg['Body'])
                    if 'Message' in event:
                        event = json.loads(event['Message'])
                    if event.get('source') != 'jobs':
                        raise ValueError('Unexpected source')
                    data = json.loads(s3.get_object(Bucket=event['bucket'], Key=event['key'])['Body'].read())
                    with conn.cursor() as cur:
                        for item in data['data']:
                            row = parse_job(item)
                            if not row[0]:
                                continue
                            cur.execute("""MERGE INTO JOB_POSTINGS t
                                USING (SELECT %s AS POSITION_ID) s ON t.POSITION_ID=s.POSITION_ID
                                WHEN MATCHED THEN UPDATE SET TITLE=%s, ORGANIZATION=%s, URL=%s,
                                    SALARY_MIN=%s, SALARY_MAX=%s
                                WHEN NOT MATCHED THEN INSERT
                                    (POSITION_ID,TITLE,ORGANIZATION,URL,SALARY_MIN,SALARY_MAX)
                                VALUES (%s,%s,%s,%s,%s,%s)""",
                                (row[0], row[1], row[2], row[3], row[4], row[5], *row))
                    conn.commit()
                    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
                except Exception:
                    conn.rollback()
                    raise  # preserve message for visibility-timeout retry
    finally:
        conn.close()

if __name__ == '__main__':
    main()
