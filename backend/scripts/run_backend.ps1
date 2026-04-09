# backend/ icinde uvicorn baslatir (calistirma dizini app paketi icin sart).
Set-Location (Join-Path $PSScriptRoot "..")
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
