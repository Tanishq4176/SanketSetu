$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3.12 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
if (-not (Test-Path '.env')) { Copy-Item .env.example .env }
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
