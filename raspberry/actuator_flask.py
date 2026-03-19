#!/usr/bin/env python3
"""Optional: simple Flask API to control the actuator ON/OFF on the Raspberry Pi.

Run this on the Raspberry Pi (not inside the API Docker container) if you want a
very lightweight HTTP interface to toggle a GPIO pin.

SECURITY
--------
This is intentionally minimal and does not implement auth by default.
If you expose it beyond localhost/LAN, add authentication (token/header) and
firewall rules.

Usage (on Raspberry Pi):
    pip install -r raspberry/requirements.txt
    ACTUATOR_GPIO_PIN=17 ACTUATOR_ACTIVE_HIGH=1 flask --app actuator_flask run --host 0.0.0.0 --port 5000

Endpoints:
    GET  /status
    POST /on
    POST /off
"""

from __future__ import annotations

import atexit

from flask import Flask, jsonify

from actuator_gpio import GPIOActuator

app = Flask(__name__)

actuator = GPIOActuator.from_env()
actuator.setup()


def _cleanup() -> None:
    try:
        actuator.cleanup()
    except Exception:
        pass


atexit.register(_cleanup)


@app.get("/status")
def status():
    return jsonify(actuator.status())


@app.post("/on")
def turn_on():
    actuator.on()
    return jsonify({"status": "ok", "message": "Actuator ON", **actuator.status()})


@app.post("/off")
def turn_off():
    actuator.off()
    return jsonify({"status": "ok", "message": "Actuator OFF", **actuator.status()})


if __name__ == "__main__":
    # For local testing without the `flask` CLI.
    app.run(host="0.0.0.0", port=5000)
