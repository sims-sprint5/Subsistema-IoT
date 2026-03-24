#!/usr/bin/env python3
"""Optional: simple Flask API to control the actuator ON/OFF on the Raspberry Pi.

Run this on the Raspberry Pi (not inside the API Docker container) if you want a
very lightweight HTTP interface to toggle a GPIO pin.

SECURITY
--------
If an API key is configured (env: IOT_API_KEY / ACTUATOR_REMOTE_API_KEY / API_KEY),
ALL endpoints require header: X-API-KEY.

Usage (on Raspberry Pi):
    pip install -r raspberry/requirements.txt
    IOT_API_KEY=supersecreta GPIO_PIN=24 ACTIVE_LOW=0 PORT=3000 python3 actuator_flask.py

Endpoints (contract):
    GET  /status
    POST /actuator         Body: {"state":"on"|"off"}
    POST /actuator/on
    POST /actuator/off

Legacy endpoints (kept for backwards compatibility):
    POST /on
    POST /off
"""

from __future__ import annotations

import atexit
import os
import signal
import sys

from flask import Flask, jsonify, request

from actuator_gpio import GPIOActuator

app = Flask(__name__)

actuator = GPIOActuator.from_env()
actuator.setup()


def _expected_api_key() -> str | None:
    # Contract expects IOT_API_KEY, but allow fallbacks for convenience.
    key = os.getenv("IOT_API_KEY") or os.getenv("ACTUATOR_REMOTE_API_KEY") or os.getenv("API_KEY")
    key = key.strip() if key else None
    return key


@app.before_request
def _require_api_key():
    expected = _expected_api_key()
    # Require auth always; if misconfigured, fail closed.
    if not expected:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    provided = request.headers.get("X-API-KEY")
    if not provided or provided != expected:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401
    return None


def _bcm_to_physical(bcm_pin: int) -> int | None:
    # Standard Raspberry Pi 40-pin header mapping (BCM -> physical).
    mapping = {
        2: 3,
        3: 5,
        4: 7,
        14: 8,
        15: 10,
        17: 11,
        18: 12,
        27: 13,
        22: 15,
        23: 16,
        24: 18,
        10: 19,
        9: 21,
        25: 22,
        11: 23,
        8: 24,
        7: 26,
        0: 27,
        1: 28,
        5: 29,
        6: 31,
        12: 32,
        13: 33,
        19: 35,
        16: 36,
        26: 37,
        20: 38,
        21: 40,
    }
    return mapping.get(bcm_pin)


def _status_payload() -> dict:
    st = actuator.status()
    # actuator.status() already normalizes state to 'on'/'off'/None
    return {
        "pin": actuator.pin,
        "active_low": (not actuator.active_high),
        "physical": _bcm_to_physical(actuator.pin),
        "state": st.get("state"),
    }


def _set_state(state: str):
    if state == "on":
        actuator.on()
        return jsonify({"ok": True, "state": "on"}), 200
    if state == "off":
        actuator.off()
        return jsonify({"ok": True, "state": "off"}), 200
    return jsonify({"ok": False, "message": "Invalid payload"}), 400


def _cleanup() -> None:
    try:
        actuator.cleanup()
    except Exception:
        pass


atexit.register(_cleanup)


@app.get("/status")
def status():
    return jsonify(_status_payload())


@app.post("/actuator")
def actuator_set():
    try:
        payload = request.get_json(silent=True) or {}
        state = payload.get("state")
        if state not in {"on", "off"}:
            return jsonify({"ok": False, "message": "Invalid payload"}), 400

        request_id = payload.get("requestId")
        ts = payload.get("ts")
        if request_id or ts:
            print(f"/actuator requestId={request_id!r} ts={ts!r} state={state}")
        return _set_state(state)
    except Exception:
        return jsonify({"ok": False, "message": "GPIO error"}), 500


@app.post("/actuator/on")
def actuator_on():
    try:
        return _set_state("on")
    except Exception:
        return jsonify({"ok": False, "message": "GPIO error"}), 500


@app.post("/actuator/off")
def actuator_off():
    try:
        return _set_state("off")
    except Exception:
        return jsonify({"ok": False, "message": "GPIO error"}), 500


@app.post("/on")
def turn_on():
    try:
        actuator.on()
        # Legacy response kept, but also includes ok/state.
        return jsonify({"ok": True, "state": "on", "status": "ok", "message": "Actuator ON", **actuator.status()})
    except Exception:
        return jsonify({"ok": False, "message": "GPIO error"}), 500


@app.post("/off")
def turn_off():
    try:
        actuator.off()
        return jsonify({"ok": True, "state": "off", "status": "ok", "message": "Actuator OFF", **actuator.status()})
    except Exception:
        return jsonify({"ok": False, "message": "GPIO error"}), 500


def _shutdown(*_args) -> None:
    try:
        actuator.cleanup()
    except Exception:
        pass
    raise SystemExit(0)


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


if __name__ == "__main__":
    # For local testing without the `flask` CLI.
    host = os.getenv("HOST", "0.0.0.0")
    port_raw = os.getenv("PORT", "3000")
    try:
        port = int(port_raw)
    except ValueError:
        print(f"Invalid PORT={port_raw!r}", file=sys.stderr)
        sys.exit(2)
    app.run(host=host, port=port)
