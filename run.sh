#!/bin/bash
# ==============================================================================
# Caramel - Script de Inicio Automático
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT="${PORT:-8001}"
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || echo "localhost")

echo -e "\033[1;33m"
echo "  ██████╗ █████╗ ██████╗  █████╗ ███╗   ███╗███████╗██╗     "
echo " ██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██╔════╝██║     "
echo " ██║     ███████║██████╔╝███████║██╔████╔██║█████╗  ██║     "
echo " ██║     ██╔══██║██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ██║     "
echo " ╚██████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║███████╗███████╗"
echo "  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝"
echo -e "\033[0m"
echo -e "\033[1;36m>> Plataforma de Recomendación de Documentos Académicos (UNIMAR)\033[0m"
echo "================================================================="

# 1. Liberar puerto 8001 si estaba ocupado
if fuser "${PORT}/tcp" >/dev/null 2>&1; then
  echo -e "\033[0;33m[*] Liberando puerto ${PORT} previamente en uso...\033[0m"
  fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
  sleep 1
fi

# 2. Activar Entorno Virtual
source venv/bin/activate

# 3. Estado de la Base de Datos
echo -e "\033[1;32m[✓] Base de Datos:\033[0m Supabase Cloud PostgreSQL (Activa 24/7 en la nube)"
echo -e "\033[1;32m[✓] Acceso Local:\033[0m  http://localhost:${PORT}"
if [ "$LOCAL_IP" != "localhost" ]; then
  echo -e "\033[1;32m[✓] Acceso WiFi:\033[0m   http://${LOCAL_IP}:${PORT} (Para tus compañeros)"
fi
echo -e "\033[0;37m-----------------------------------------------------------------\033[0m"
echo -e "\033[1;35m[*] Presiona Ctrl+C en cualquier momento para detener.\033[0m"
echo "================================================================="

# 4. Abrir automáticamente en el navegador tras 1.5s (si xdg-open está disponible)
if command -v xdg-open >/dev/null 2>&1 && [ "$1" != "--no-browser" ]; then
  (sleep 1.5 && xdg-open "http://localhost:${PORT}" >/dev/null 2>&1) &
fi

# 5. Ejecutar Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
