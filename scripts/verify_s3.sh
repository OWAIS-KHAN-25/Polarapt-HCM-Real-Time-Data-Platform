#!/usr/bin/env bash
set -euo pipefail
BUCKET="${S3_BUCKET_NAME:-data-hackathon-smit-owais}"
REGION="${AWS_REGION:-us-east-1}"
for prefix in jobs benchmarks fx; do
  echo "== raw/$prefix =="
  aws s3 ls "s3://$BUCKET/raw/$prefix/" --recursive --region "$REGION"
done
