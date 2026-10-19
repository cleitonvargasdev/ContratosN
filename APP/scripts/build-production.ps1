$ErrorActionPreference = 'Stop'
$appRoot = Split-Path $PSScriptRoot -Parent
$flutter = Join-Path (Split-Path $appRoot -Parent) 'flutter-sdk\bin\flutter.bat'
if (-not (Test-Path -LiteralPath (Join-Path $appRoot 'android\key.properties'))) {
    throw 'Configure a assinatura release em android/key.properties antes de compilar.'
}
$previousJavaOptions = $env:JAVA_TOOL_OPTIONS
try {
    # Usa as autoridades já confiáveis do Windows, sem desativar TLS.
    $env:JAVA_TOOL_OPTIONS = '-Djavax.net.ssl.trustStoreType=Windows-ROOT -Djavax.net.ssl.trustStore=NONE'
    Push-Location $appRoot
    try {
        & $flutter build apk --release --dart-define-from-file=config/production.json
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar o APK.' }
    } finally { Pop-Location }
} finally {
    $env:JAVA_TOOL_OPTIONS = $previousJavaOptions
}
