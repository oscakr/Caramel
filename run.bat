@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Caramel - Plataforma Académica UNIMAR

cls
echo =================================================================
echo.
echo    ######     ###    ########     ###    ##     ## ######## ##       
echo   ##    ##   ## ##   ##     ##   ## ##   ###   ### ##       ##       
echo   ##        ##   ##  ##     ##  ##   ##  #### #### ##       ##       
echo   ##       ##     ## ########  ##     ## ## ### ## ######   ##       
echo   ##       ######### ##   ##   ######### ##     ## ##       ##       
echo   ##    ## ##     ## ##    ##  ##     ## ##     ## ##       ##       
echo    ######  ##     ## ##     ## ##     ## ##     ## ######## ######## 
echo.
echo  -- Plataforma de Recomendacion Academica UNIMAR (ISO 21001) --
echo =================================================================

set "PORT=8001"
if not "%~1"=="" set "PORT=%~1"

REM Determinar ejecutable de Python
set "PY=python"
if exist "%~dp0venv\Scripts\python.exe" (
    set "PY=%~dp0venv\Scripts\python.exe"
)

echo [OK] Puerto configurado: %PORT%
echo [OK] Base de Datos: caramel.db (o Supabase si existe .env)
echo [OK] Acceso Web:   http://localhost:%PORT%
echo -----------------------------------------------------------------
echo [*] Abriendo navegador y arrancando servidor FastAPI...
echo [*] Presiona Ctrl+C para detener.
echo =================================================================

REM Abrir navegador en 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:%PORT%/login"

REM Arrancar Uvicorn
"%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload

pause
