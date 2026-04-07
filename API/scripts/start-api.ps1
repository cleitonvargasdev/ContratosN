$ErrorActionPreference = 'Stop'

Set-Location 'D:\PROJETOINI\API'

if (-not (Test-Path '.\.venv\Scripts\Activate.ps1')) {
    throw 'Virtual environment not found at .venv\Scripts\Activate.ps1'
}

. .\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = 'D:/PROJETOINI/API'

& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8006