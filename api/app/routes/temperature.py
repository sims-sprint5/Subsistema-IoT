"""
Rutas para recibir datos de la Raspberry Pi.
La Raspberry envía lecturas de temperatura por HTTP POST.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.schemas import TemperatureCreate, TemperatureResponse, MessageResponse
from app.database import get_database
from app.auth import verify_api_key

router = APIRouter(prefix="/api/temperature", tags=["Raspberry Pi"])


@router.post("/", response_model=MessageResponse)
async def create_temperature(data: TemperatureCreate, _: str = Depends(verify_api_key)):
    """
    Recibe lectura de temperatura desde la Raspberry Pi y la guarda en MongoDB.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    document = {
        "adc_value": data.adc_value,
        "voltage": data.voltage,
        "temperature_c": data.temperature_c,
        "timestamp": datetime.now(timezone.utc),
    }

    result = await db["temperatura"].insert_one(document)

    return MessageResponse(
        message=f"Lectura guardada con id: {str(result.inserted_id)}",
        status="ok",
    )


@router.post("/bulk", response_model=MessageResponse)
async def create_temperatures_bulk(
    readings: list[TemperatureCreate], _: str = Depends(verify_api_key)
):
    """
    Recibe múltiples lecturas de temperatura (envío por lotes).
    Útil si la Raspberry pierde conexión y acumula lecturas.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    documents = [
        {
            "adc_value": r.adc_value,
            "voltage": r.voltage,
            "temperature_c": r.temperature_c,
            "timestamp": datetime.now(timezone.utc),
        }
        for r in readings
    ]

    result = await db["temperatura"].insert_many(documents)

    return MessageResponse(
        message=f"{len(result.inserted_ids)} lecturas guardadas",
        status="ok",
    )
