"""
WebSocket routes for real-time bidirectional communication with IoT devices (Raspberry Pis).
"""
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

from app.ws_manager import manager
from app.database import get_database
from app.config import LARAVEL_API_URL, LARAVEL_API_KEY

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/vehicle/{vehicle_id}")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: str):
    await manager.connect(vehicle_id, websocket)
    try:
        while True:
            # Esperem rebre dades del vehicle (ex: sensors)
            data = await websocket.receive_json()
            
            if data.get("type") == "temperature":
                document = {
                    "vehicle_id": vehicle_id,
                    "adc_value": data.get("adc_value"),
                    "voltage": data.get("voltage"),
                    "temperature_c": data.get("temperature_c"),
                    "timestamp": datetime.now(timezone.utc),
                }

                # Guardem la lectura a MongoDB (si disponible)
                inserted_id = None
                db = get_database()
                if db is not None:
                    try:
                        result = await db["temperatura"].insert_one(document)
                        inserted_id = result.inserted_id
                    except Exception as e:
                        print(f"WS: Failed to store temperature in MongoDB: {e}")

                # Reenviament opcional a Laravel
                if LARAVEL_API_URL and inserted_id is not None:
                    try:
                        async with httpx.AsyncClient() as client:
                            headers = {"Accept": "application/json"}
                            if LARAVEL_API_KEY:
                                headers["Authorization"] = f"Bearer {LARAVEL_API_KEY}"

                            doc_to_send = document.copy()
                            doc_to_send["_id"] = str(inserted_id)
                            doc_to_send["timestamp"] = doc_to_send["timestamp"].isoformat()

                            await client.post(
                                f"{LARAVEL_API_URL.rstrip('/')}/temperatures",
                                json=doc_to_send,
                                headers=headers,
                                timeout=5.0
                            )
                    except Exception as e:
                        print(f"WS: Failed to forward to Laravel: {e}")

    except WebSocketDisconnect:
        manager.disconnect(vehicle_id)
