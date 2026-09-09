#!/bin/bash
# Caramel Run Script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Iniciando Caramel - Recomendador de Documentos Académicos"
echo "=========================================================="

# Activate Virtualenv
source venv/bin/activate

# Start Server
echo "Servidor corriendo en: http://localhost:8000"
echo "Documentación API:     http://localhost:8000/docs"
echo "Presiona Ctrl+C para detener."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
