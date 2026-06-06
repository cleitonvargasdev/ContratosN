param(
    [Parameter(Mandatory=$true)]
    [string]$Mensagem
)

$repos = @(
    "D:\PROJETOINI\API",
    "D:\PROJETOINI\FRONTEND"
)

foreach ($repo in $repos) {

    Write-Host ""
    Write-Host "Processando: $repo"

    Set-Location $repo

    $branch = git branch --show-current

    git add -A

    if (git diff --cached --quiet) {
        Write-Host "Nenhuma alteração."
        continue
    }

    git commit -m $Mensagem
    git push origin $branch
}

Write-Host ""
Write-Host "Finalizado."