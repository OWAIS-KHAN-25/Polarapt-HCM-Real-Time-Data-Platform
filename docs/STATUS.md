# Implementation status

**Last updated:** 25 October 2026.

## Verified on AWS via user-provided outputs

- Jobs: `lambda_jobs_ingest` returned 500 and uploaded `raw/jobs/2026/10/24/2225.json`.
- Benchmarks: `lambda_benchmarks_scraper-owais` returned 10 and uploaded `raw/benchmarks/2026/10/24/2318.json`.
- FX: `lambda_fx_ingest-owais` returned 6 and uploaded `raw/fx/2026/10/24/2330.json`.
- SNS Standard topic `hackathon-s3-events-owais` created; S3 bucket publish policy saved.

## Not yet verified/deployed

- S3 ObjectCreated notification to SNS (`raw/`, `.json`).
- SNS subscription to router Lambda, router IAM permissions, FIFO topic and subscriptions.
- Three SQS FIFO queues and queue policies, DLQs, message filtering.
- Processing Lambdas, Glue job, SQL Server, Snowflake.
- EventBridge schedules, integration tests, monitoring, costs.

## Source fidelity

The assignment requires BLS highest-paying top 10. Current scraper uses O*NET **10 selected occupations**, sorted by annual median pay. This is a documented deviation, not an equivalent BLS top-ten ranking.

## Code provenance

The benchmarks and FX ingestion scripts reproduce code discussed and deployed during the hackathon chat. The jobs ingestion script is a **reference reconstruction** of the verified behavior, not a byte-for-byte export of the live Lambda. All downstream code is **new reference implementation** and requires deployment, credentials, networking, and testing.
