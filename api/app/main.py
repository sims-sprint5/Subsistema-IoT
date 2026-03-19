"""
FastAPI - IoT Subsystem
Intermediary API between Raspberry Pi and MongoDB.
Also exposes endpoints for Laravel to consume the data.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection
from app.routes.temperature import router as temperature_router
from app.routes.laravel import router as laravel_router
from app.routes.actuator import router as actuator_router
from app.actuator import get_or_create_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle connection to MongoDB at app startup/shutdown."""
    await connect_to_mongo()

    # Optional GPIO actuator setup (safe: disabled by default).
    controller = get_or_create_controller()
    controller.startup()
    app.state.actuator_controller = controller

    yield

    # Best-effort cleanup.
    try:
        controller.shutdown()
    except Exception:
        pass
    await close_mongo_connection()


app = FastAPI(
    title="Subsistema IoT API",
    description=(
        "API to receive sensor data from Raspberry Pi, "
        "store it in MongoDB and expose it to Laravel."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(temperature_router)
app.include_router(laravel_router)
app.include_router(actuator_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check."""
    return {"status": "ok", "service": "Subsistema IoT API"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    from app.database import get_database

    db = get_database()
    mongo_ok = db is not None

    return {
        "status": "ok" if mongo_ok else "degraded",
        "mongodb": "connected" if mongo_ok else "disconnected",
    }
