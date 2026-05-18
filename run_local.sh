#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=8080}"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" --reload
