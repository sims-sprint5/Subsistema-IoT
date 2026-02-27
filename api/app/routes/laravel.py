"""
Rutas para que Laravel consuma datos de temperatura.
Incluye listado paginado, filtros por fecha, estadísticas y última lectura.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from app.schemas import (
    TemperatureResponse,
    TemperatureListResponse,
    StatsResponse,
    MessageResponse,
)
from app.database import get_database
from app.auth import verify_api_key

router = APIRouter(prefix="/api/laravel", tags=["Laravel"])


def format_temperature(doc: dict) -> dict:
    """Convierte documento de MongoDB a formato de respuesta."""
    doc["_id"] = str(doc["_id"])
    return doc


# ==================== LISTADO PAGINADO ====================

@router.get("/temperatures", response_model=TemperatureListResponse)
async def list_temperatures(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    start_date: Optional[datetime] = Query(None, description="Fecha inicio (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Fecha fin (ISO 8601)"),
    _: str = Depends(verify_api_key),
):
    """
    Listado paginado de lecturas de temperatura.
    Laravel puede filtrar por rango de fechas.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    # Construir filtro
    query = {}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
        if not query["timestamp"]:
            del query["timestamp"]

    # Contar total
    total = await db["temperatura"].count_documents(query)

    # Obtener página
    skip = (page - 1) * per_page
    cursor = (
        db["temperatura"]
        .find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(per_page)
    )

    data = []
    async for doc in cursor:
        data.append(format_temperature(doc))

    return TemperatureListResponse(
        total=total,
        page=page,
        per_page=per_page,
        data=data,
    )


# ==================== ÚLTIMA LECTURA ====================

@router.get("/temperatures/latest", response_model=TemperatureResponse)
async def get_latest_temperature(_: str = Depends(verify_api_key)):
    """Obtiene la lectura de temperatura más reciente."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    doc = await db["temperatura"].find_one(sort=[("timestamp", -1)])

    if not doc:
        raise HTTPException(status_code=404, detail="No hay lecturas de temperatura")

    return format_temperature(doc)


# ==================== LECTURA POR ID ====================

@router.get("/temperatures/{temperature_id}", response_model=TemperatureResponse)
async def get_temperature_by_id(
    temperature_id: str, _: str = Depends(verify_api_key)
):
    """Obtiene una lectura de temperatura por su ID."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        doc = await db["temperatura"].find_one({"_id": ObjectId(temperature_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    if not doc:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    return format_temperature(doc)


# ==================== ESTADÍSTICAS ====================

@router.get("/temperatures/stats/summary", response_model=StatsResponse)
async def get_temperature_stats(
    start_date: Optional[datetime] = Query(None, description="Fecha inicio (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Fecha fin (ISO 8601)"),
    _: str = Depends(verify_api_key),
):
    """
    Estadísticas de temperatura: promedio, mínimo, máximo, total.
    Laravel puede usarlas para dashboards.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    # Filtro por fecha
    match_stage = {}
    if start_date or end_date:
        match_stage["timestamp"] = {}
        if start_date:
            match_stage["timestamp"]["$gte"] = start_date
        if end_date:
            match_stage["timestamp"]["$lte"] = end_date

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.append(
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avg_temperature": {"$avg": "$temperature_c"},
                "min_temperature": {"$min": "$temperature_c"},
                "max_temperature": {"$max": "$temperature_c"},
            }
        }
    )

    result = await db["temperatura"].aggregate(pipeline).to_list(1)

    if not result:
        return StatsResponse(count=0)

    stats = result[0]

    # Obtener última lectura
    last_doc = await db["temperatura"].find_one(sort=[("timestamp", -1)])
    last_reading = format_temperature(last_doc) if last_doc else None

    return StatsResponse(
        count=stats["count"],
        avg_temperature=round(stats["avg_temperature"], 2) if stats["avg_temperature"] else None,
        min_temperature=round(stats["min_temperature"], 2) if stats["min_temperature"] else None,
        max_temperature=round(stats["max_temperature"], 2) if stats["max_temperature"] else None,
        last_reading=last_reading,
    )


# ==================== ELIMINAR LECTURAS ====================

@router.delete("/temperatures", response_model=MessageResponse)
async def delete_temperatures(
    start_date: Optional[datetime] = Query(None, description="Fecha inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha fin"),
    _: str = Depends(verify_api_key),
):
    """Eliminar lecturas de temperatura por rango de fechas."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    query = {}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Debes especificar al menos start_date o end_date para eliminar",
        )

    result = await db["temperatura"].delete_many(query)

    return MessageResponse(
        message=f"{result.deleted_count} lecturas eliminadas", status="ok"
    )
