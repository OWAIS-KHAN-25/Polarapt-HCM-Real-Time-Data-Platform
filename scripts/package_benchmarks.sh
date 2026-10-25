#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/benchmarks
python3 -m pip install -r ingestion/benchmarks/requirements.txt --target build/benchmarks
cp ingestion/benchmarks/lambda_function.py build/benchmarks/lambda_function.py
(cd build/benchmarks && zip -qr ../../benchmarks_lambda.zip .)
echo "Created benchmarks_lambda.zip (do not commit generated ZIP)"
