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

    @staticmethod
    def disabled_default() -> "ActuatorConfig":
        # Safe defaults. Pin is only informational when disabled.
        return ActuatorConfig(enabled=False, gpio_pin=24, active_high=True, simulate=False)

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
        return ActuatorConfig(
            enabled=enabled,
            gpio_pin=gpio_pin,
            active_high=active_high,
            simulate=simulate,
        )


class ActuatorController:
    """High-level actuator interface used by the API."""

    def __init__(self, config: ActuatorConfig):
        self._config = config
        self._lock = threading.Lock()
        self._gpio = None  # late import of RPi.GPIO
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
            self._available = True
            self._state = False
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
        return {
            "enabled": self.enabled,
            "available": self.available,
            "state": ("on" if self._state else "off") if self._state is not None else None,
            "gpio_pin": self._config.gpio_pin,
            "active_high": self._config.active_high,
            "simulated": self.simulated,
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

        GPIO = self._gpio
        assert GPIO is not None

        level = GPIO.HIGH if self._level_for(state_on) else GPIO.LOW
        GPIO.output(self._config.gpio_pin, level)
        self._state = state_on


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
