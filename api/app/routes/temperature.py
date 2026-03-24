"""
Routes to receive data from the Raspberry Pi.
The Raspberry sends temperature readings via HTTP POST.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import httpx

from app.schemas import TemperatureCreate, TemperatureResponse, MessageResponse
from app.database import get_database
from app.auth import verify_api_key
from app.config import LARAVEL_API_URL, LARAVEL_API_KEY

router = APIRouter(prefix="/api/temperature", tags=["Raspberry Pi"])


@router.post("/", response_model=MessageResponse)
async def create_temperature(data: TemperatureCreate, _: str = Depends(verify_api_key)):
    """
    Receives temperature reading from the Raspberry Pi and saves it in MongoDB,
    and forwards it to the Laravel Backend.
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

    # Forward to Laravel via HTTP
    try:
        if LARAVEL_API_URL:
            async with httpx.AsyncClient() as client:
                headers = {"Accept": "application/json"}
                if LARAVEL_API_KEY:
                    headers["Authorization"] = f"Bearer {LARAVEL_API_KEY}"
                
                document_to_send = document.copy()
                document_to_send["_id"] = str(result.inserted_id)
                document_to_send["timestamp"] = document_to_send["timestamp"].isoformat()
                
                await client.post(
                    f"{LARAVEL_API_URL.rstrip('/')}/temperatures",
                    json=document_to_send,
                    headers=headers,
                    timeout=5.0
                )
    except Exception as e:
        # We don't want to fail the Raspberry's request if Laravel is down, so just log it.
        print(f"Failed to forward reading to Laravel: {e}")

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
    Forwards them to MongoDB and Laravel.
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
    
    try:
        if LARAVEL_API_URL:
            async with httpx.AsyncClient() as client:
                headers = {"Accept": "application/json"}
                if LARAVEL_API_KEY:
                    headers["Authorization"] = f"Bearer {LARAVEL_API_KEY}"
                
                # Zip the inserted IDs with the documents
                for i, doc in enumerate(documents):
                    doc["_id"] = str(result.inserted_ids[i])
                    doc["timestamp"] = doc["timestamp"].isoformat()

                await client.post(
                    f"{LARAVEL_API_URL.rstrip('/')}/temperatures/bulk",
                    json=documents,
                    headers=headers,
                    timeout=10.0
                )
    except Exception as e:
        print(f"Failed to forward bulk readings to Laravel: {e}")

    return MessageResponse(
        message=f"{len(result.inserted_ids)} readings saved",
        status="ok",
    )
