"""Actuator control endpoints.

These endpoints are protected by the same X-API-Key mechanism used for sensor
posting, to avoid accidental/unauthorized physical actuation.

Endpoints:
- GET  /api/actuator           -> status
- POST /api/actuator/on        -> turn ON
- POST /api/actuator/off       -> turn OFF
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.actuator import ActuatorController, ActuatorUnavailableError, get_or_create_controller
from app.auth import verify_api_key
from app.schemas import ActuatorCommandResponse, ActuatorStatusResponse

router = APIRouter(prefix="/api/actuator", tags=["Actuator"])


def _get_controller(request: Request) -> ActuatorController:
    controller = getattr(request.app.state, "actuator_controller", None)
    if controller is None:
        # Fallback for cases where startup hook didn't run.
        controller = get_or_create_controller()
        controller.startup()
        request.app.state.actuator_controller = controller
    return controller


@router.get("/", response_model=ActuatorStatusResponse)
def actuator_status(request: Request, _: str = Depends(verify_api_key)):
    controller = _get_controller(request)
    return ActuatorStatusResponse(**controller.status())


@router.post("/on", response_model=ActuatorCommandResponse)
def actuator_on(request: Request, _: str = Depends(verify_api_key)):
    controller = _get_controller(request)
    try:
        controller.on()
    except ActuatorUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ActuatorCommandResponse(message="Actuator turned ON", status="ok", state="on")


@router.post("/off", response_model=ActuatorCommandResponse)
def actuator_off(request: Request, _: str = Depends(verify_api_key)):
    controller = _get_controller(request)
    try:
        controller.off()
    except ActuatorUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ActuatorCommandResponse(message="Actuator turned OFF", status="ok", state="off")
