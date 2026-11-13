#!/bin/bash
# ==============================================================================
# Caramel - Script de Control Inteligente
# Modos:
#   caramel         -> Inicia en terminal interactiva con banner y abre navegador
#   caramel start   -> Inicia en segundo plano, envía notificación y abre navegador
#   caramel stop    -> Detiene el servidor y libera el puerto
#   caramel status  -> Muestra si está encendido o apagado
#   caramel restart -> Reinicia el servidor limpiamente
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT="${PORT:-8001}"
PID_FILE="$DIR/.caramel.pid"
LOG_FILE="$DIR/.caramel.log"
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || echo "localhost")

print_banner() {
  echo -e "\033[1;33m"
  echo "  ██████╗ █████╗ ██████╗  █████╗ ███╗   ███╗███████╗██╗     "
  echo " ██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██╔════╝██║     "
  echo " ██║     ███████║██████╔╝███████║██╔████╔██║█████╗  ██║     "
  echo " ██║     ██╔══██║██╔══██╗██╔══██║██║╚██╔╝██║██╔══╝  ██║     "
  echo " ╚██████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║███████╗███████╗"
  echo "  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝"
  echo -e "\033[0m"
  echo -e "\033[1;36m>> Plataforma de Recomendación Académica UNIMAR (ISO 21001)\033[0m"
  echo "================================================================="
}

start_foreground() {
  print_banner

  if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    echo -e "\033[0;33m[*] Liberando puerto ${PORT} ocupado anteriormente...\033[0m"
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
    sleep 1
  fi

  source venv/bin/activate
  echo -e "\033[1;32m[OK] Base de Datos:\033[0m Supabase Cloud PostgreSQL (Activa 24/7 en la nube)"
  echo -e "\033[1;32m[OK] Acceso Local:\033[0m  http://localhost:${PORT}"
  if [ "$LOCAL_IP" != "localhost" ]; then
    echo -e "\033[1;32m[OK] Acceso WiFi:\033[0m   http://${LOCAL_IP}:${PORT} (Para tus compañeros)"
  fi
  echo -e "\033[0;37m-----------------------------------------------------------------\033[0m"
  echo -e "\033[1;35m[*] Presiona Ctrl+C en cualquier momento para detener.\033[0m"
  echo "================================================================="

  wait_and_open_browser "$1"

  exec "$DIR/venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
}

wait_and_open_browser() {
  if [ "$1" = "--no-browser" ]; then
    return 0
  fi
  (
    for i in {1..40}; do
      if curl -s -m 1 "http://127.0.0.1:${PORT}/login" >/dev/null 2>&1; then
        if command -v notify-send >/dev/null 2>&1; then
          notify-send "Caramel Listo" "Plataforma activa en http://localhost:${PORT}" -i applications-education 2>/dev/null || true
        fi
        if command -v xdg-open >/dev/null 2>&1; then
          xdg-open "http://localhost:${PORT}/login" >/dev/null 2>&1 &
        fi
        break
      fi
      sleep 0.5
    done
  ) &
}

start_background() {
  if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    echo -e "\033[1;32m[OK] Caramel ya está corriendo en http://localhost:${PORT}\033[0m"
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "http://localhost:${PORT}/login" >/dev/null 2>&1 &
    fi
    exit 0
  fi

  nohup "$DIR/venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"

  echo "================================================================="
  echo -e "\033[1;32m[OK] Conectando con Supabase e iniciando servidor...\033[0m"
  echo -e "\033[1;32m[OK] Base de Datos:\033[0m Supabase Cloud PostgreSQL (24/7)"
  echo -e "\033[1;32m[OK] Acceso Local:\033[0m  http://localhost:${PORT}"
  if [ "$LOCAL_IP" != "localhost" ]; then
    echo -e "\033[1;32m[OK] Acceso WiFi:\033[0m   http://${LOCAL_IP}:${PORT}"
  fi
  echo -e "\033[0;37mPara detenerlo ejecuta: caramel stop\033[0m"
  echo "================================================================="

  wait_and_open_browser "$1"
}

stop_server() {
  if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
    rm -f "$PID_FILE"
    echo -e "\033[1;32m[OK] Servidor Caramel detenido correctamente.\033[0m"
    if command -v notify-send >/dev/null 2>&1; then
      notify-send "Caramel" "Servidor detenido correctamente." -i applications-education 2>/dev/null || true
    fi
  else
    echo -e "\033[0;33m[*] No hay ningún servidor Caramel activo en el puerto ${PORT}.\033[0m"
  fi
}

status_server() {
  if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    echo -e "\033[1;32m[OK] Caramel está ACTIVO y corriendo en el puerto ${PORT}\033[0m"
    echo "    Local: http://localhost:${PORT}"
    echo "    WiFi:  http://${LOCAL_IP}:${PORT}"
  else
    echo -e "\033[1;31m[ERROR] Caramel está DETENIDO.\033[0m"
  fi
}

case "$1" in
  start)
    start_background
    ;;
  stop)
    stop_server
    ;;
  restart)
    stop_server
    sleep 1
    start_background
    ;;
  status)
    status_server
    ;;
  *)
    start_foreground "$@"
    ;;
esac
