#!/usr/bin/env bash
set -euo pipefail

# Aquest script arrenca el Webhook, obté la URL del Cloudflare Fast Tunnel 
# i posa en marxa l'enviament del sensor, tot en un sol procés. No utilitza .env externs.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ================================
# CONFIGURACIÓ (Claus al mateix script)
# ================================
API_KEY_SECRETA="subsistemaequip2"
API_URL_DESTI="http://192.168.1.100:8008/api/temperature" # <- CANVIA AIXÒ A LA IP/URL DE LA TEVA API

echo "==> 1. Iniciant Webhook (Actuador)..."
export IOT_API_KEY="$API_KEY_SECRETA"
export GPIO_PIN=24
export ACTIVE_LOW=0
export PORT=3000

python3 "$DIR/actuator_flask.py" > "$DIR/actuator.log" 2>&1 &
ACTUATOR_PID=$!

echo "==> 2. Creant nou Fast Tunnel de Cloudflare..."
# Obrim el tunnel cap al port 3000 de l'actuador
cloudflared tunnel --url http://127.0.0.1:3000 > "$DIR/cloudflare.log" 2>&1 &
TUNNEL_PID=$!

echo "Esperant a qué Cloudflare ens doni la URL pública (5 segons)..."
sleep 5
TUNNEL_URL=$(grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" "$DIR/cloudflare.log" | head -n 1)

if [ -z "$TUNNEL_URL" ]; then
    echo "⚠️ ALERTA: No s'ha pogut obtenir la URL. Revisa cloudflare.log"
else
    echo "=========================================================================="
    echo "✅ TÚNEL CREADO AMB ÈXIT!"
    echo "URL per l'Actuador: $TUNNEL_URL"
    echo "--> Has d'afegir aquesta URL al .env del backend com ACTUATOR_REMOTE_URL"
    echo "=========================================================================="
fi

echo "==> 3. Iniciant l'enviament de dades del Sensor..."
export API_KEY="$API_KEY_SECRETA"
export API_URL="$API_URL_DESTI"
export SEND_INTERVAL=10

python3 "$DIR/thermistor.py" > "$DIR/sensor.log" 2>&1 &
SENSOR_PID=$!

echo "✅ Sistema IoT funcionant! (Prem Ctrl+C per tancar-ho tot)"

# Capturar Ctrl+C per tancar correctament els 3 processos
trap "echo -e '\nAturant processos...'; kill $ACTUATOR_PID $TUNNEL_PID $SENSOR_PID; exit" SIGINT SIGTERM

# Esperar que els processos acabin per no tancar l'script
wait
