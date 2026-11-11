# Caramel - Script de Control para Windows PowerShell
param(
    [string]$Port = "8001"
)

$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $dir

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

Write-Host "[✓] Entorno: Windows PowerShell" -ForegroundColor Cyan
Write-Host "[✓] Base de Datos: caramel.db (SQLite) / PostgreSQL Cloud" -ForegroundColor Green
Write-Host "[✓] Acceso Local:  http://localhost:$Port" -ForegroundColor Green
Write-Host "[*] Presiona Ctrl+C en cualquier momento para detener." -ForegroundColor White
Write-Host "================================================================="

# Lanzar apertura de navegador en segundo plano
Start-Job -ScriptBlock {
    param($p)
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:$p/login"
} -ArgumentList $Port | Out-Null

& $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
