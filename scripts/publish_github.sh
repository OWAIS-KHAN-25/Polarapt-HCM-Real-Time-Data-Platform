#!/usr/bin/env bash
# Run locally after reviewing the repo and authenticating with gh auth login.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v gh >/dev/null; then echo 'Install GitHub CLI: https://cli.github.com/'; exit 1; fi
if [ -f .env ]; then echo 'Reminder: .env is ignored by Git. Do not force-add it.'; fi
git init
git add .
git commit -m 'Initial Polarapt HCM hackathon project structure'
gh repo create polarapt-hcm-real-time-data-platform --public --source=. --remote=origin --push
