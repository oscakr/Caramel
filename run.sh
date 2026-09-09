#!/bin/bash
# Caramel Run Script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT="${PORT:-8000}"

echo "=========================================================="
echo " Caramel - Plataforma Académica & Algoritmo de Recomendación"
echo "=========================================================="

# Check if port is in use and free it if needed
if fuser "${PORT}/tcp" >/dev/null 2>&1; then
  echo "Liberando el puerto ${PORT} ocupado anteriormente..."
  fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
  sleep 1
fi

# Activate Virtualenv
source venv/bin/activate

echo "🚀 Servidor iniciado exitosamente en: http://localhost:${PORT}"
echo "📊 Laboratorio del Algoritmo:       http://localhost:${PORT}/recommender-lab"
echo "📚 Documentación Swagger API:       http://localhost:${PORT}/docs"
echo "Presiona Ctrl+C para detener el servidor."
echo "----------------------------------------------------------"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
