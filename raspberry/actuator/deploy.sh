#!/usr/bin/env bash
set -euo pipefail

# Aquest script instal·la les dependències, arrenca el Webhook 
# i posa en marxa l'enviament del sensor.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ================================
# CONFIGURACIÓ (Claus al mateix script)
# ================================
API_KEY_SECRETA="joelrubio06"
API_URL_DESTI="http://192.168.1.100:8008/api/temperature" # <- CANVIA AIXÒ A LA IP/URL DE LA TEVA API

echo "==> 1. Verificant dependències (requirements.txt)..."
pip3 install -r "$DIR/requirements.txt" > /dev/null 2>&1 || echo "Avís: No s'ha pogut executar pip install. Assegura't de tenir les dependències."

echo "==> 2. Iniciant Webhook (Actuador)..."
export IOT_API_KEY="$API_KEY_SECRETA"
export GPIO_PIN=24
export ACTIVE_LOW=0
export PORT=3000

python3 "$DIR/actuator_flask.py" > "$DIR/actuator.log" 2>&1 &
ACTUATOR_PID=$!

echo "==> 3. Iniciant l'enviament de dades del Sensor..."
export API_KEY="$API_KEY_SECRETA"
export API_URL="$API_URL_DESTI"
export SEND_INTERVAL=10

python3 "$DIR/thermistor.py" > "$DIR/sensor.log" 2>&1 &
SENSOR_PID=$!

echo "=========================================================================="
echo "✅ PROCESSOS INICIATS AMB ÈXIT!"
echo "   - Actuador (Port 3000) -> PID: $ACTUATOR_PID"
echo "   - Sensor de Temperatura -> PID: $SENSOR_PID"
echo ""
echo "⚠️ Recorda crear el Fast Tunnel tu mateix apuntant al port 3000:"
echo "   cloudflared tunnel --url http://127.0.0.1:3000"
echo "=========================================================================="
echo "Prem Ctrl+C per tancar el Sensor i l'Actuador alhora."

# Capturar Ctrl+C per tancar correctament els processos
trap "echo -e '\nAturant processos...'; kill $ACTUATOR_PID $SENSOR_PID; exit" SIGINT SIGTERM

# Esperar que els processos acabin per no tancar l'script
wait
