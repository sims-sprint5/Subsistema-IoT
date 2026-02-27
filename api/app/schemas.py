from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== Schemas para recibir datos de la Raspberry ==========

class TemperatureCreate(BaseModel):
    """Datos que envía la Raspberry Pi."""
    adc_value: int = Field(..., ge=0, le=255, description="Valor ADC (0-255)")
    voltage: float = Field(..., ge=0, description="Voltaje calculado")
    temperature_c: float = Field(..., description="Temperatura en Celsius")


# ========== Schemas de respuesta ==========

class TemperatureResponse(BaseModel):
    """Respuesta con datos de temperatura."""
    id: str = Field(..., alias="_id")
    adc_value: int
    voltage: float
    temperature_c: float
    timestamp: datetime

    class Config:
        populate_by_name = True


class TemperatureListResponse(BaseModel):
    """Respuesta con lista de temperaturas (para Laravel)."""
    total: int
    page: int
    per_page: int
    data: list[TemperatureResponse]


class StatsResponse(BaseModel):
    """Estadísticas de temperatura (para Laravel)."""
    count: int
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    last_reading: Optional[TemperatureResponse] = None


class MessageResponse(BaseModel):
    """Respuesta genérica con mensaje."""
    message: str
    status: str = "ok"
