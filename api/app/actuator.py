"""GPIO ON/OFF actuator control (Raspberry Pi).

This module is intentionally defensive:
- If GPIO libraries aren't available (e.g. running in Docker on a laptop), it will
  expose a "disabled/unavailable" actuator rather than crashing the API.
- Default behavior is safe: actuator starts OFF and must be explicitly enabled
  via env var.

WIRING / SAFETY NOTES (read before connecting real loads)
--------------------------------------------------------
1) LED (safe demo)
   - Use a series resistor (220–1kΩ).
   - GPIO -> resistor -> LED anode (+), LED cathode (-) -> GND.

2) Relay module (typical 5V relay board)
   - Do NOT power the relay coil directly from the GPIO.
   - Use a relay module with a transistor/optocoupler driver.
   - Many relay modules are "active LOW". Set ACTUATOR_ACTIVE_HIGH=0 if so.
   - Power the relay module from 5V and GND, and connect IN to the chosen GPIO.

3) Motor / inductive loads
   - Never connect a motor directly to GPIO.
   - Use a transistor/MOSFET driver and a flyback diode (for DC motors/solenoids).

DISCLAIMER
----------
Always verify your module logic level, pinout, and load current requirements.
A wrong wiring can permanently damage the Raspberry Pi.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Optional

import json


class ActuatorUnavailableError(RuntimeError):
    pass


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class ActuatorConfig:
    enabled: bool
    gpio_pin: int
    active_high: bool
    simulate: bool
    remote_url: Optional[str]
    remote_timeout_s: float
    remote_api_key: Optional[str]

    @staticmethod
    def disabled_default() -> "ActuatorConfig":
        # Safe defaults. Pin is only informational when disabled.
        return ActuatorConfig(
            enabled=False,
            gpio_pin=24,
            active_high=True,
            simulate=False,
            remote_url=None,
            remote_timeout_s=2.5,
            remote_api_key=None,
        )

    @staticmethod
    def from_env() -> "ActuatorConfig":
        enabled = _parse_bool(os.getenv("ACTUATOR_ENABLED", "0"), default=False)
        gpio_pin_raw = os.getenv("ACTUATOR_GPIO_PIN", "24")
        try:
            gpio_pin = int(gpio_pin_raw)
        except ValueError as exc:
            raise ValueError(f"Invalid ACTUATOR_GPIO_PIN={gpio_pin_raw!r}") from exc

        active_high = _parse_bool(os.getenv("ACTUATOR_ACTIVE_HIGH", "1"), default=True)
        simulate = _parse_bool(os.getenv("ACTUATOR_SIMULATE", "0"), default=False)

        remote_url = os.getenv("ACTUATOR_REMOTE_URL")
        remote_url = remote_url.strip() if remote_url else None

        remote_timeout_raw = os.getenv("ACTUATOR_REMOTE_TIMEOUT", "2.5")
        try:
            remote_timeout_s = float(remote_timeout_raw)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ACTUATOR_REMOTE_TIMEOUT={remote_timeout_raw!r} (must be float seconds)"
            ) from exc

        # Header key for remote actuator service.
        # Defaults to the same API_KEY used by this API (convenient single secret).
        remote_api_key = os.getenv("ACTUATOR_REMOTE_API_KEY")
        if remote_api_key is None:
            remote_api_key = os.getenv("API_KEY")
        remote_api_key = remote_api_key.strip() if remote_api_key else None

        return ActuatorConfig(
            enabled=enabled,
            gpio_pin=gpio_pin,
            active_high=active_high,
            simulate=simulate,
            remote_url=remote_url,
            remote_timeout_s=remote_timeout_s,
            remote_api_key=remote_api_key,
        )


class ActuatorController:
    """High-level actuator interface used by the API."""

    def __init__(self, config: ActuatorConfig):
        self._config = config
        self._lock = threading.Lock()
        self._gpio = None  # late import of RPi.GPIO
        self._remote = None  # late import of httpx.Client
        self._available = False
        self._state: Optional[bool] = None  # True=ON, False=OFF, None=unknown/unavailable

    @property
    def config(self) -> ActuatorConfig:
        return self._config

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    @property
    def available(self) -> bool:
        return self._available

    @property
    def simulated(self) -> bool:
        return self._config.simulate

    def startup(self) -> None:
        """Setup GPIO and ensure a safe initial OFF state."""

        if not self._config.enabled:
            self._available = False
            self._state = None
            return

        # Development mode: simulate without touching GPIO.
        # Useful when running the API on a PC/WSL/Docker.
        if self._config.simulate:
            self._gpio = None
            self._remote = None
            self._available = True
            self._state = False
            return

        # Remote mode: delegate ON/OFF to a Raspberry Pi HTTP endpoint.
        # This allows running the API on a PC while the Pi toggles GPIO.
        if self._config.remote_url:
            try:
                import httpx  # type: ignore

                self._remote = httpx.Client(
                    base_url=self._config.remote_url,
                    timeout=self._config.remote_timeout_s,
                    headers=self._remote_headers(),
                )
            except Exception:
                self._remote = None
                self._available = False
                self._state = None
                return

            # Best-effort probe.
            try:
                self._remote_status_probe()
            except Exception:
                self._available = False
                self._state = None
            return

        try:
            import RPi.GPIO as GPIO  # type: ignore

            self._gpio = GPIO
        except Exception:
            # Running somewhere without GPIO support (e.g., non-RPi or container).
            self._gpio = None
            self._available = False
            self._state = None
            return

        with self._lock:
            GPIO = self._gpio
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            # Safe default: OFF.
            initial_level = GPIO.HIGH if self._level_for(False) else GPIO.LOW
            GPIO.setup(self._config.gpio_pin, GPIO.OUT, initial=initial_level)

            self._available = True
            self._state = False

    def shutdown(self) -> None:
        """Best-effort cleanup.

        Note: when running as a long-lived web server, we do NOT call cleanup per
        request. Cleanup happens at process shutdown.
        """

        if self._remote is not None:
            try:
                self._remote.close()
            except Exception:
                pass
            self._remote = None

        if not self._gpio:
            return

        with self._lock:
            GPIO = self._gpio
            try:
                # Put into safe OFF state before cleanup.
                self._write_locked(False)
            finally:
                try:
                    GPIO.cleanup(self._config.gpio_pin)
                except Exception:
                    # Best-effort.
                    pass

            self._available = False
            self._state = None

    def status(self) -> dict:
        # In remote mode, refresh status best-effort.
        if self._remote is not None:
            try:
                self._remote_status_probe()
            except Exception:
                # Leave previous state; mark as unavailable.
                self._available = False
                self._state = None

        return {
            "enabled": self.enabled,
            "available": self.available,
            "state": ("on" if self._state else "off") if self._state is not None else None,
            "gpio_pin": self._config.gpio_pin,
            "active_high": self._config.active_high,
            "simulated": self.simulated,
            "remote_url": self._config.remote_url,
        }

    def on(self) -> None:
        self._ensure_available()
        with self._lock:
            self._write_locked(True)

    def off(self) -> None:
        self._ensure_available()
        with self._lock:
            self._write_locked(False)

    def _ensure_available(self) -> None:
        if not self.enabled:
            raise ActuatorUnavailableError(
                "Actuator disabled. Set ACTUATOR_ENABLED=1 to enable GPIO control."
            )

        if self._config.simulate:
            # Always available when simulating.
            return

        if self._remote is not None:
            if not self._available:
                raise ActuatorUnavailableError(
                    "Actuator unavailable (remote endpoint not reachable)."
                )
            return

        if not self._gpio or not self._available:
            raise ActuatorUnavailableError(
                "Actuator unavailable (GPIO library not present or no hardware access)."
            )

    def _level_for(self, state_on: bool) -> int:
        """Return 1 for HIGH, 0 for LOW for desired actuator state."""
        if self._config.active_high:
            return 1 if state_on else 0
        # active-low relay modules
        return 0 if state_on else 1

    def _write_locked(self, state_on: bool) -> None:
        if self._config.simulate:
            self._state = state_on
            return

        if self._remote is not None:
            self._remote_set_state(state_on)
            return

        GPIO = self._gpio
        assert GPIO is not None

        level = GPIO.HIGH if self._level_for(state_on) else GPIO.LOW
        GPIO.output(self._config.gpio_pin, level)
        self._state = state_on

    def _remote_status_probe(self) -> None:
        client = self._remote
        if client is None:
            return
        resp = client.get("/status")
        if resp.status_code >= 400:
            raise ActuatorUnavailableError(
                f"Remote actuator returned HTTP {resp.status_code}"
            )

        data = self._safe_json(resp.text)
        state = data.get("state")
        if isinstance(state, dict):
            state = state.get("state")
        if state == "on":
            self._state = True
        elif state == "off":
            self._state = False
        else:
            self._state = None

        self._available = True

    def _remote_set_state(self, state_on: bool) -> None:
        client = self._remote
        if client is None:
            raise ActuatorUnavailableError("Remote actuator client not initialized.")

        # Preferred API (Node/Express spec): POST /actuator/on|off (auth via X-API-KEY)
        endpoint = "/actuator/on" if state_on else "/actuator/off"
        try:
            resp = client.post(endpoint)
        except Exception as exc:
            self._available = False
            self._state = None
            raise ActuatorUnavailableError(f"Remote actuator request failed: {exc}") from exc

        # Backwards-compatibility: older Flask version used POST /on|/off
        if resp.status_code == 404:
            legacy_endpoint = "/on" if state_on else "/off"
            try:
                resp = client.post(legacy_endpoint)
            except Exception as exc:
                self._available = False
                self._state = None
                raise ActuatorUnavailableError(f"Remote actuator request failed: {exc}") from exc

        if resp.status_code >= 400:
            self._available = False
            self._state = None
            raise ActuatorUnavailableError(
                f"Remote actuator returned HTTP {resp.status_code}"
            )

        data = self._safe_json(resp.text)
        state = data.get("state")
        if state is None:
            state = data.get("data", {}).get("state") if isinstance(data.get("data"), dict) else None
        if state == "on":
            self._state = True
        elif state == "off":
            self._state = False
        else:
            # Fallback to requested state.
            self._state = state_on

        self._available = True

    @staticmethod
    def _safe_json(text: str) -> dict:
        try:
            payload = json.loads(text)
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _remote_headers(self) -> dict:
        # Service requires X-API-KEY according to the user's spec.
        if not self._config.remote_api_key:
            return {}
        return {"X-API-KEY": self._config.remote_api_key}


# Singleton-style controller for the FastAPI app.
_controller: Optional[ActuatorController] = None
_controller_error: Optional[str] = None


def get_or_create_controller() -> ActuatorController:
    global _controller
    global _controller_error
    if _controller is None:
        try:
            config = ActuatorConfig.from_env()
        except Exception as exc:
            # Never break the whole API due to actuator configuration.
            _controller_error = str(exc)
            config = ActuatorConfig.disabled_default()

        _controller = ActuatorController(config)
    return _controller


def get_controller_error() -> Optional[str]:
    return _controller_error


def reset_controller_for_tests() -> None:
    """Testing hook (not used in prod)."""
    global _controller
    global _controller_error
    _controller = None
    _controller_error = None
