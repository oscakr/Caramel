@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Caramel - Plataforma Académica UNIMAR

cls
echo =================================================================
echo   ██████╗ █████╗ ██████╗  █████╗ ███╗   ███╗███████╗██╗     
echo  ██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██╔════╝██║     
echo  ██║     ███████║██████╔╝███████║██╔████╔██║█████╗  ██║     
echo  ██║     ██╔══██║██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ██║     
echo  ╚██████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║███████╗███████╗
echo   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝
echo  >> Plataforma de Recomendacion Academica UNIMAR (ISO 21001)
echo =================================================================

set PORT=8001
if not "%1"=="" set PORT=%1

:: Buscar interprete de Python
set "PY=python"
if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
)

echo [✓] Puerto configurado: %PORT%
echo [✓] Base de Datos: caramel.db (o Supabase si existe .env)
echo [✓] Acceso Web:   http://localhost:%PORT%
echo -----------------------------------------------------------------
echo [*] Abriendo navegador y arrancando servidor FastAPI...
echo [*] Presiona Ctrl+C para detener.
echo =================================================================

:: Abrir navegador en 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:%PORT%/login"

:: Arrancar Uvicorn
%PY% -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload

pause
