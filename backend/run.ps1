# Dev server. Usage:  .\run.ps1
$ErrorActionPreference = "Stop"
if (-not (Test-Path .venv)) { py -3.10 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env from .env.example - add your GEMINI_API_KEYS" }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
