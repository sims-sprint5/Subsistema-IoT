"""
Routes to receive data from the Raspberry Pi.
The Raspberry sends temperature readings via HTTP POST.
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
    Receives temperature reading from the Raspberry Pi and saves it in MongoDB.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    document = {
        "adc_value": data.adc_value,
        "voltage": data.voltage,
        "temperature_c": data.temperature_c,
        "timestamp": datetime.now(timezone.utc),
    }

    result = await db["temperatura"].insert_one(document)

    return MessageResponse(
        message=f"Reading saved with id: {str(result.inserted_id)}",
        status="ok",
    )


@router.post("/bulk", response_model=MessageResponse)
async def create_temperatures_bulk(
    readings: list[TemperatureCreate], _: str = Depends(verify_api_key)
):
    """
    Receives multiple temperature readings (batch sending).
    Useful if the Raspberry loses connection and accumulates readings.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

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
        message=f"{len(result.inserted_ids)} readings saved",
        status="ok",
    )
