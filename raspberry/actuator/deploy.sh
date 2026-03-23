#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
REMOTE_DIR="${2:-/opt/actuator}"
SERVICE_NAME="actuator"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 user@host [remote_dir]"
  echo "Example: $0 pi@192.168.226.139 /opt/actuator"
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Deploying to $TARGET:$REMOTE_DIR"

ssh -o BatchMode=no "$TARGET" "sudo mkdir -p '$REMOTE_DIR' && sudo chown -R \"$USER\":\"$USER\" '$REMOTE_DIR' || true"

rsync -av --delete \
  "$ROOT_DIR/actuator_flask.py" \
  "$ROOT_DIR/actuator_gpio.py" \
  "$ROOT_DIR/requirements.txt" \
  "$TARGET:$REMOTE_DIR/"

ssh -o BatchMode=no "$TARGET" "set -euo pipefail
  cd '$REMOTE_DIR'
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt

  if [[ ! -f actuator.env ]]; then
    cat > actuator.env <<'ENV'
# Required
IOT_API_KEY=CAMBIA_ESTA_CLAVE

# GPIO (BCM)
GPIO_PIN=24
# ACTIVE_LOW=1 para relés active-low (muy comunes). Para active-high: 0
ACTIVE_LOW=0

# HTTP
HOST=0.0.0.0
PORT=3000
ENV
    echo "Created $REMOTE_DIR/actuator.env (EDITA IOT_API_KEY!)"
  fi

  sudo tee /etc/systemd/system/${SERVICE_NAME}.service >/dev/null <<UNIT
[Unit]
Description=GPIO Actuator HTTP Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$REMOTE_DIR
EnvironmentFile=$REMOTE_DIR/actuator.env
ExecStart=$REMOTE_DIR/.venv/bin/python $REMOTE_DIR/actuator_flask.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT

  sudo systemctl daemon-reload
  sudo systemctl enable --now ${SERVICE_NAME}.service
  sudo systemctl restart ${SERVICE_NAME}.service
  sudo systemctl --no-pager --full status ${SERVICE_NAME}.service | head -n 25
"

echo "==> Done. Test from your PC:"
echo "curl http://<RPI_IP>:3000/status -H 'X-API-KEY: TU_CLAVE'"
