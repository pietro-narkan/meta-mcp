$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$RepoDir = (Get-Location).Path

Write-Host "▶ (1/5) Verificando uv..."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "    Instalando uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host "▶ (2/5) Instalando dependencias..."
uv sync

if (-not (Test-Path .env)) {
    Write-Host "▶ (3/5) Configurando token de solo-lectura..."
    Copy-Item .env.example .env
    $Secure = Read-Host "    Pega tu token de SOLO LECTURA de Meta" -AsSecureString
    $Token = [System.Net.NetworkCredential]::new("", $Secure).Password
    $escaped = $Token -replace '([$])', '$$$1'
    (Get-Content .env) -replace '^META_ACCESS_TOKEN=.*', "META_ACCESS_TOKEN=$escaped" | Set-Content .env
    Write-Host "    Token guardado en .env"
} else {
    Write-Host "▶ (3/5) .env ya existe, lo dejo como está."
}

Write-Host "▶ (4/5) Generando .mcp.json..."
$mcp = [ordered]@{
    mcpServers = [ordered]@{
        "meta-ads" = [ordered]@{
            command = "uv"
            args    = @("--directory", $RepoDir, "run", "python", "-m", "meta_ads_mcp")
        }
    }
}
$mcp | ConvertTo-Json -Depth 6 | Set-Content .mcp.json

Write-Host "▶ (5/5) Health-check..."
uv run python scripts/healthcheck.py

Write-Host ""
Write-Host "✅ Listo. Abre Claude Code en esta carpeta y pregunta."
