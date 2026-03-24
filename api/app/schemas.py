from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== Schemas to receive data from the Raspberry ==========

class TemperatureCreate(BaseModel):
    """Data sent by the Raspberry Pi."""
    adc_value: int = Field(..., ge=0, le=255, description="ADC Value (0-255)")
    voltage: float = Field(..., ge=0, description="Calculated voltage")
    temperature_c: float = Field(..., description="Temperature in Celsius")


# ========== Response schemas ==========

class TemperatureResponse(BaseModel):
    """Response with temperature data."""
    id: str = Field(..., alias="_id")
    adc_value: int
    voltage: float
    temperature_c: float
    timestamp: datetime

    class Config:
        populate_by_name = True


class TemperatureListResponse(BaseModel):
    """Response with temperature list (for Laravel)."""
    total: int
    page: int
    per_page: int
    data: list[TemperatureResponse]


class StatsResponse(BaseModel):
    """Temperature stats (for Laravel)."""
    count: int
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    last_reading: Optional[TemperatureResponse] = None


class MessageResponse(BaseModel):
    """Generic response with message."""
    message: str
    status: str = "ok"


# ========== Actuator schemas ==========

class ActuatorStatusResponse(BaseModel):
    """Current actuator status and configuration."""

    enabled: bool
    available: bool
    state: Optional[str] = Field(
        default=None,
        description="Current state: 'on' | 'off' | null (unknown/unavailable)",
    )
    gpio_pin: int = Field(..., description="BCM GPIO pin number")
    active_high: bool = Field(
        ..., description="True if GPIO HIGH means actuator ON (active-high)"
    )

    simulated: Optional[bool] = Field(
        default=None,
        description="True if actuator is in simulation mode (no real GPIO/remote calls)",
    )

    remote_url: Optional[str] = Field(
        default=None,
        description="If set, actuator is delegated to this remote HTTP service",
    )


class ActuatorCommandResponse(MessageResponse):
    """Response for ON/OFF commands."""

    state: str = Field(..., description="Resulting state: 'on' | 'off'")
