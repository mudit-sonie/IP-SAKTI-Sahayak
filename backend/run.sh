#!/usr/bin/env bash
# Dev server. Usage:  ./run.sh
set -euo pipefail
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example - add your GEMINI_API_KEYS"; }
./.venv/bin/python -m uvicorn app.main:app --reload --host :: --port 8000
