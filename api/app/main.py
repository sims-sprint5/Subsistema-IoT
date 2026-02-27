"""
FastAPI - Subsistema IoT
API intermediaria entre Raspberry Pi y MongoDB.
También expone endpoints para que Laravel consuma los datos.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection
from app.routes.temperature import router as temperature_router
from app.routes.laravel import router as laravel_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejar conexión a MongoDB al iniciar/cerrar la app."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Subsistema IoT API",
    description=(
        "API para recibir datos de sensores desde Raspberry Pi, "
        "almacenarlos en MongoDB y exponerlos a Laravel."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Registrar routers
app.include_router(temperature_router)
app.include_router(laravel_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check."""
    return {"status": "ok", "service": "Subsistema IoT API"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check detallado."""
    from app.database import get_database

    db = get_database()
    mongo_ok = db is not None

    return {
        "status": "ok" if mongo_ok else "degraded",
        "mongodb": "connected" if mongo_ok else "disconnected",
    }
