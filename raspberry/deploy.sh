#!/usr/bin/env bash
set -euo pipefail

# Aquest script instal·la les dependències, arrenca el Webhook 
# i posa en marxa l'enviament del sensor.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ================================
# CONFIGURACIÓ (Claus al mateix script)
# ================================
API_KEY_SECRETA="subsistemaequip2"

echo "==> 1. Verificant dependències (requirements.txt)..."
pip3 install -r "$DIR/raspberry/requirements.txt" > /dev/null 2>&1 || echo "Avís: No s'ha pogut executar pip install. Assegura't de tenir les dependències."

echo "==> 2. Iniciant Client WebSocket (Sensor + Actuador)..."
export IOT_API_KEY="$API_KEY_SECRETA"
export API_WS_URL="ws://<LA-URL-DEL-DOCKER-TUNEL>/ws/vehicle/001"
export VEHICLE_ID="001"
export GPIO_PIN=24
export ACTIVE_LOW=0

python3 "$DIR/raspberry/client_ws.py" > "$DIR/raspberry/client_ws.log" 2>&1 &
WS_PID=$!

echo "=========================================================================="
echo "✅ PROCESSOS INICIATS AMB ÈXIT!"
echo "   - Client WebSocket IoT -> PID: $WS_PID"
echo ""
echo "⚠️ Recorda canviar <LA-URL-DEL-DOCKER-TUNEL> per la URL del cloudflared"
echo "   que hi ha al PC corrent (per exemple: wss://nom.trycloudflare.com)"
echo "=========================================================================="
echo "Prem Ctrl+C per tancar el procés."

# Capturar Ctrl+C per tancar correctament els processos
trap "echo -e '\nAturant processos...'; kill $WS_PID; exit" SIGINT SIGTERM

# Esperar que els processos acabin per no tancar l'script
wait
