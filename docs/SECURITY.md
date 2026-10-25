# Security and cost checklist

- Never commit API keys, AWS credentials, tokens, `.env`, secrets, account access keys, or SQL Server passwords.
- Rotate any credential previously pasted into chats or screenshots.
- Use least-privilege IAM policies; restrict SNS topic publish permission by `aws:SourceArn` and `aws:SourceAccount`.
- Enable S3 Block Public Access; do not publish raw HR records publicly.
- Encrypt secrets and destination traffic; SQL Server uses `Encrypt=yes;TrustServerCertificate=no`.
- Prefer Secrets Manager for credentials in production.
- SQS FIFO delivery is at least once end-to-end; consumers must be idempotent.
- Avoid self-triggering S3 event loops by restricting notifications to `raw/` only; processors write to `processed/`.
- Avoid enabling minute-level schedules until quotas and costs are reviewed.
- GitHub secret scanning should be enabled where available.
