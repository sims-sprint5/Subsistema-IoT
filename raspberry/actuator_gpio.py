"""Minimal ON/OFF actuator control via Raspberry Pi GPIO.

This is intended to run *on the Raspberry Pi*.

WIRING / SAFETY
---------------
LED demo (recommended first test):
- Use a resistor (220–1kΩ).
- GPIO (BCM pin) -> resistor -> LED anode (+)
- LED cathode (-) -> GND

Relay module:
- Use a relay board with a driver transistor/optocoupler.
- Many relay boards are "active LOW". Set active_high=False for those.

Motor / inductive loads:
- Never connect directly to GPIO.
- Use a MOSFET/transistor driver + flyback diode.

Environment variables (optional):
- ACTUATOR_GPIO_PIN (default 17)
- ACTUATOR_ACTIVE_HIGH (default 1)

Example:
    from actuator_gpio import GPIOActuator

    a = GPIOActuator(pin=17, active_high=True)
    a.setup()
    a.on()
    ...
    a.cleanup()
"""

from __future__ import annotations

import os
import threading
from typing import Optional


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class GPIOActuator:
    def __init__(self, pin: int = 24, active_high: bool = True):
        self.pin = pin
        self.active_high = active_high
        self._gpio = None
        self._lock = threading.Lock()
        self._state: Optional[bool] = None

    @classmethod
    def from_env(cls) -> "GPIOActuator":
        pin = int(os.getenv("ACTUATOR_GPIO_PIN", "24"))
        active_high = _parse_bool(os.getenv("ACTUATOR_ACTIVE_HIGH", "1"), default=True)
        return cls(pin=pin, active_high=active_high)

    def setup(self) -> None:
        import RPi.GPIO as GPIO  # type: ignore

        self._gpio = GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Safe default: OFF.
        initial_level = GPIO.HIGH if self._level_for(False) else GPIO.LOW
        GPIO.setup(self.pin, GPIO.OUT, initial=initial_level)
        self._state = False

    def cleanup(self) -> None:
        if not self._gpio:
            return

        with self._lock:
            try:
                self.off()
            finally:
                try:
                    self._gpio.cleanup(self.pin)
                except Exception:
                    pass
                self._gpio = None
                self._state = None

    def status(self) -> dict:
        return {
            "gpio_pin": self.pin,
            "active_high": self.active_high,
            "state": ("on" if self._state else "off") if self._state is not None else None,
        }

    def on(self) -> None:
        self._ensure_ready()
        with self._lock:
            self._write_locked(True)

    def off(self) -> None:
        self._ensure_ready()
        with self._lock:
            self._write_locked(False)

    def _ensure_ready(self) -> None:
        if not self._gpio:
            raise RuntimeError("GPIO not initialized. Call setup() first.")

    def _level_for(self, state_on: bool) -> int:
        if self.active_high:
            return 1 if state_on else 0
        return 0 if state_on else 1

    def _write_locked(self, state_on: bool) -> None:
        GPIO = self._gpio
        assert GPIO is not None
        level = GPIO.HIGH if self._level_for(state_on) else GPIO.LOW
        GPIO.output(self.pin, level)
        self._state = state_on
