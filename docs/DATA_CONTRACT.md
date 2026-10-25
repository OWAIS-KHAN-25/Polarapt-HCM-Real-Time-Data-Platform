# Raw data contract

Every object is UTF-8 JSON with top-level `metadata`:

```json
{
  "metadata": {
    "source": "open_exchange_rates",
    "timestamp": "2026-10-24T23:30:27+00:00",
    "record_count": 6,
    "response_status": 200
  },
  "base_currency": "USD",
  "api_timestamp": 1792882801,
  "rates": {"PKR": 276.527559, "SAR": 3.75325, "AED": 3.6725, "GBP": 0.747692, "EUR": 0.892538, "INR": 94.94655}
}
```

The above is an example from a **historical user-verified test**, not a live FX quote.

### Source identifiers

- Jobs: `jobs` (reconstructed example code; confirm against live Lambda S3 metadata)
- Benchmarks: `onet_occupational_wages`
- FX: `open_exchange_rates`

### Downstream routing

The router normalizes `onet_occupational_wages` -> `benchmarks` and `open_exchange_rates` -> `fx`. Route is based on S3 object metadata obtained with `HeadObject`, not guessed from filenames alone.

### Caution

S3 metadata keys are lowercased by S3. Values are strings. S3 event notifications contain bucket/key and object details but **not custom S3 object metadata**, which is why the router performs `HeadObject`.
