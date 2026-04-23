#!/usr/bin/env bash
set -euo pipefail

# Aquest script instal·la les dependències i arrenca el 
# Client IoT WebSocket (Sensor + Actuador).

# Aquesta línia apunta al directori ACTUAL d'aquest script (/raspberry)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ================================
# CONFIGURACIÓ (Claus al mateix script)
# ================================
API_KEY_SECRETA="subsistemaequip2"

echo "==> 1. Verificant dependències (requirements.txt)..."
pip3 install -r "$DIR/requirements.txt" > /dev/null 2>&1 || echo "Avís: No s'ha pogut executar pip install. Assegura't de tenir les dependències."

echo "==> 2. Iniciant Client WebSocket IoT (Sensor + Actuador)..."
export IOT_API_KEY="$API_KEY_SECRETA"
export API_WS_URL="wss://lexmark-scenarios-anything-accordance.trycloudflare.com/ws/vehicle/001"
export VEHICLE_ID="001"
export GPIO_PIN=24
export ACTIVE_LOW=0

# Executem el procés de fons i n'amaguem la sortida i errors a client_ws.log
python3 "$DIR/client_ws.py" > "$DIR/client_ws.log" 2>&1 &
WS_PID=$!

echo "=========================================================================="
echo "✅ PROCESSOS INICIATS AMB ÈXIT!"
echo "   - Client WebSocket IoT -> PID: $WS_PID"
echo ""
echo "📝 Comprova els logs del client en temps real fent:"
echo "   tail -f client_ws.log"
echo "=========================================================================="
echo "Prem Ctrl+C per tancar el procés central."

# Capturar Ctrl+C per tancar correctament els processos fons
trap "echo -e '\nAturant processos...'; kill $WS_PID; exit" SIGINT SIGTERM

# Esperar que els processos acabin per no tancar l'script pare
wait
