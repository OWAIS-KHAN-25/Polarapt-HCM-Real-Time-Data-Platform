# Deployment guide — continue from Step 9.3

## 0. Safety first

- Confirm account/region `us-east-1`; verify costs and quotas before scheduling.
- Do not put API keys in GitHub. Set Lambda environment variables, preferably backed by AWS Secrets Manager for production.
- Review the AWS account number in `infrastructure/sns-topic-policy.json` before reusing it in another account.

## 1. Ingestion (already manually verified in original AWS account)

- Jobs Lambda: `lambda_jobs_ingest`, variables `USAJOBS_EMAIL`, `USAJOBS_API_KEY`, `S3_BUCKET_NAME`.
- Benchmarks Lambda: `lambda_benchmarks_scraper-owais`, variable `S3_BUCKET_NAME`, Python dependencies packaged via `scripts/package_benchmarks.sh`; timeout at least 60 seconds, review page latency.
- FX Lambda: `lambda_fx_ingest-owais`, variables `OPENEXCHANGE_APP_ID`, `S3_BUCKET_NAME`.
- IAM `s3:PutObject` scoped to each `raw/<source>/*` prefix; CloudWatch Logs permissions.

## 2. S3 -> SNS Standard (next live step)

- Existing SNS topic: `hackathon-s3-events-owais` (Standard).
- Existing topic policy includes S3 publish permission for bucket `data-hackathon-smit-owais`.
- S3 console > bucket > Properties > Event notifications > Create notification.
- Name: `raw-data-upload-notification`; prefix `raw/`; suffix `.json`; event: All object create events; destination SNS topic `hackathon-s3-events-owais`.
- Avoid overlapping notification rules with the same prefix/suffix/event; AWS may reject overlaps.
- Save and verify using a small test JSON upload. At this stage SNS has no subscription, so downstream delivery is not yet expected.

## 3. SNS Standard -> router Lambda

- Create `hcm-s3-event-router-owais` Python Lambda from `routing/router_lambda/lambda_function.py`.
- Environment variable `ROUTED_TOPIC_ARN` with ARN of SNS FIFO topic from next step.
- IAM: CloudWatch logs, `s3:HeadObject` equivalent `s3:GetObject` on `raw/*`, and `sns:Publish` on FIFO topic.
- Subscribe router Lambda to Standard topic with protocol **AWS Lambda**. Verify resource-based invoke permission is created.
- Test event and CloudWatch logs before enabling recurring ingestion.

## 4. SNS FIFO and SQS FIFO

- Create SNS FIFO topic `hcm-routed-events.fifo`.
- Create FIFO queues `jobs-queue.fifo`, `benchmarks-queue.fifo`, `fx-queue.fifo` and source-specific FIFO DLQs.
- Allow SNS FIFO topic to `sqs:SendMessage` in each queue resource policy (limit by topic ARN).
- Subscribe each queue to SNS FIFO topic; use message-attribute filter policies in `infrastructure/sqs-filter-policies/`.
- Ensure filter policy scope is `MessageAttributes`; router sends `source` message attribute.
- FIFO message group ID is the source; deduplication ID is based on bucket/key/sequencer.
- Confirm raw message delivery setting and use the processor's wrapper-aware parsing.

## 5. Processing destinations

- Benchmarks processor `processing/benchmarks/lambda_function.py` writes `processed/benchmarks/`; SQS event-source mapping should enable `ReportBatchItemFailures`.
- FX processor `processing/fx/lambda_function.py` needs SQL Server host, schema, credentials, ODBC Driver 18, `pyodbc` binary-compatible layer/container, and network access. Configure event-source mapping with `ReportBatchItemFailures`.
- Jobs Glue Python Shell job `processing/jobs_glue/glue_job.py` needs Snowflake Python connector, queue URL, AWS permissions, Snowflake schema and network access. Trigger with EventBridge only after verifying queue polling and timeout/visibility settings.
- **SQS messages must only be deleted after successful durable destination write.** Lambda SQS event-source mapping handles deletion automatically on successful processing; the Glue sample explicitly deletes after commit.

## 6. Scheduling and costs

- Do **not** enable minute-level FX polling blindly. A 1-minute cadence is ~43,200 calls per 30-day month, well beyond a typical free-tier limit of ~1,000/month.
- Review terms of use and page scraping limits for O*NET; prefer infrequent benchmark refresh.
- The original assignment asks for every-minute triggers; document and agree on a quota-aware demo approach with the instructor.
- Monitor Lambda invocations/errors, SQS queue age, SNS deliveries, Glue DPU charges, SQL Server/Snowflake usage.
