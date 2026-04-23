"""Actuator control endpoints.

These endpoints are protected by the same X-API-Key mechanism used for sensor
posting, to avoid accidental/unauthorized physical actuation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import verify_api_key
from app.schemas import ActuatorCommandResponse, ActuatorStatusResponse
from app.ws_manager import manager

router = APIRouter(prefix="/api/actuator", tags=["Actuator"])

@router.get("/{vehicle_id}/status", response_model=ActuatorStatusResponse)
def actuator_status(vehicle_id: str, _: str = Depends(verify_api_key)):
    is_connected = vehicle_id in manager.active_connections
    return ActuatorStatusResponse(
        enabled=True,
        available=is_connected,
        state=None,  # State is managed by the device now
        gpio_pin=24,
        active_high=True,
        simulated=False,
        remote_url=f"ws://.../ws/vehicle/{vehicle_id}"
    )

@router.post("/{vehicle_id}/on", response_model=ActuatorCommandResponse)
async def actuator_vehicle_on(vehicle_id: str, _: str = Depends(verify_api_key)):
    success = await manager.send_command(vehicle_id, {"command": "ON"})
    if not success:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not connected")
    return ActuatorCommandResponse(message=f"Actuator ON sent to vehicle {vehicle_id}", status="ok", state="on")

@router.post("/{vehicle_id}/off", response_model=ActuatorCommandResponse)
async def actuator_vehicle_off(vehicle_id: str, _: str = Depends(verify_api_key)):
    success = await manager.send_command(vehicle_id, {"command": "OFF"})
    if not success:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not connected")
    return ActuatorCommandResponse(message=f"Actuator OFF sent to vehicle {vehicle_id}", status="ok", state="off")
