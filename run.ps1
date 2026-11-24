# Caramel - Script de Control para Windows PowerShell
param(
    [ValidateSet("local", "online", "auto")]
    [string]$Mode = "auto",
    [string]$Port = "8001"
)

$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $dir

$prevDbMode = $env:CARAMEL_DB_MODE
$prevDbUrl  = $env:DATABASE_URL

try {
    Write-Host @"
  ██████╗ █████╗ ██████╗  █████╗ ███╗   ███╗███████╗██╗     
 ██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██╔════╝██║     
 ██║     ███████║██████╔╝███████║██╔████╔██║█████╗  ██║     
 ██║     ██╔══██║██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ██║     
 ╚██████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║███████╗███████╗
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝
>> Plataforma de Recomendación Académica UNIMAR (ISO 21001)
=================================================================
"@ -ForegroundColor Yellow

    $pythonExe = "python"
    if (Test-Path "$dir\venv\Scripts\python.exe") {
        $pythonExe = "$dir\venv\Scripts\python.exe"
    }

    if ($Mode -eq "local") {
        $env:CARAMEL_DB_MODE = "local"
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
        $dbLabel = "LOCAL -> caramel.db (SQLite, modo rápido)"
        $dbColor = "Green"
    }
    elseif ($Mode -eq "online") {
        $env:CARAMEL_DB_MODE = "online"
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
        if (-not (Test-Path "$dir\.env")) {
            Write-Host "[ERROR] No se encontró el archivo .env con la URL de Supabase." -ForegroundColor Red
            exit 1
        }
        $dbLabel = "ONLINE -> Supabase PostgreSQL Cloud (.env)"
        $dbColor = "Cyan"
    }
    else {
        Remove-Item Env:CARAMEL_DB_MODE -ErrorAction SilentlyContinue
        $dbLabel = "AUTO -> Según .env (o caramel.db si no existe .env)"
        $dbColor = "Yellow"
    }

    Write-Host "[OK] Entorno:       Windows PowerShell" -ForegroundColor Cyan
    Write-Host "[OK] Base de Datos: $dbLabel" -ForegroundColor $dbColor
    Write-Host "[OK] Acceso Local:  http://localhost:$Port" -ForegroundColor Green
    Write-Host "[*] Presiona Ctrl+C en cualquier momento para detener." -ForegroundColor White
    Write-Host "================================================================="

    # Lanzar apertura de navegador en segundo plano
    $browserJob = Start-Job -ScriptBlock {
        param($p)
        Start-Sleep -Seconds 2
        Start-Process "http://localhost:$p/login"
    } -ArgumentList $Port

    & $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
}
finally {
    if ($browserJob) {
        Remove-Job -Job $browserJob -Force -ErrorAction SilentlyContinue
    }
    if ($null -eq $prevDbMode) {
        Remove-Item Env:CARAMEL_DB_MODE -ErrorAction SilentlyContinue
    } else {
        $env:CARAMEL_DB_MODE = $prevDbMode
    }
    if ($null -eq $prevDbUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:DATABASE_URL = $prevDbUrl
    }
    Pop-Location
}
