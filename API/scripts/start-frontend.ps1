$ErrorActionPreference = 'Stop'

$frontendPath = 'D:\PROJETOINI\FRONTEND'

if (-not (Test-Path $frontendPath)) {
    throw "Frontend path not found: $frontendPath"
}

Set-Location $frontendPath

if (-not (Test-Path '.\node_modules')) {
    Write-Host 'node_modules not found. Running npm install...'
    npm install
}

npm run dev