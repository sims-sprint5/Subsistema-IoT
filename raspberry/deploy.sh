#!/usr/bin/env bash
set -euo pipefail

# This script install dependences and start websocket (Sensor & Actuator)

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 1. Checking dependencies (requirements.txt)..."
pip3 install -r "$DIR/requirements.txt" > /dev/null 2>&1 || echo "Warning: Could not run pip install. Make sure dependencies are available."

echo "==> 2. Loading environment variables (.env)..."
if [ -f "$DIR/.env" ]; then
    sed -i 's/\r$//' "$DIR/.env"
    set -a
    . "$DIR/.env"
    set +a
else
    echo "❌ Error: .env file not found. Rename .env.example to .env"
    exit 1
fi

echo "==> 3. Starting IoT WebSocket Client (Sensor + Actuator)..."
python3 "$DIR/client_ws.py" > "$DIR/client_ws.log" 2>&1 &
WS_PID=$!

echo "=========================================================================="
echo "✅ PROCESSES STARTED SUCCESSFULLY!"
echo "   - IoT WebSocket Client -> PID: $WS_PID"
echo ""
echo "📝 Check the client logs in real-time with:"
echo "   tail -f client_ws.log"
echo "=========================================================================="
echo "Press Ctrl+C to stop the main process."

trap "echo -e '\nStopping processes...'; kill $WS_PID; exit" SIGINT SIGTERM

wait
