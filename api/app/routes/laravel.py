"""
Routes for Laravel to consume temperature data.
Includes paginated list, date filters, stats and latest reading.
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
    """Converts MongoDB document to response format."""
    doc["_id"] = str(doc["_id"])
    return doc


# ==================== PAGINATED LIST ====================

@router.get("/temperatures", response_model=TemperatureListResponse)
async def list_temperatures(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    _: str = Depends(verify_api_key),
):
    """
    Paginated list of temperature readings.
    Laravel can filter by date range.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    # Build filter
    query = {}
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
        if not query["timestamp"]:
            del query["timestamp"]

    # Count total
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


# ==================== LATEST READING ====================

@router.get("/temperatures/latest", response_model=TemperatureResponse)
async def get_latest_temperature(_: str = Depends(verify_api_key)):
    """Gets the most recent temperature reading."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    doc = await db["temperatura"].find_one(sort=[("timestamp", -1)])

    if not doc:
        raise HTTPException(status_code=404, detail="No temperature readings")

    return format_temperature(doc)


# ==================== READING BY ID ====================

@router.get("/temperatures/{temperature_id}", response_model=TemperatureResponse)
async def get_temperature_by_id(
    temperature_id: str, _: str = Depends(verify_api_key)
):
    """Gets a temperature reading by its ID."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    try:
        doc = await db["temperatura"].find_one({"_id": ObjectId(temperature_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Reading not found")

    return format_temperature(doc)


# ==================== STATS ====================

@router.get("/temperatures/stats/summary", response_model=StatsResponse)
async def get_temperature_stats(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    _: str = Depends(verify_api_key),
):
    """
    Temperature stats: average, minimum, maximum, total.
    Laravel can use them for dashboards.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    # Date filter
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

    # Get latest reading
    last_doc = await db["temperatura"].find_one(sort=[("timestamp", -1)])
    last_reading = format_temperature(last_doc) if last_doc else None

    return StatsResponse(
        count=stats["count"],
        avg_temperature=round(stats["avg_temperature"], 2) if stats["avg_temperature"] else None,
        min_temperature=round(stats["min_temperature"], 2) if stats["min_temperature"] else None,
        max_temperature=round(stats["max_temperature"], 2) if stats["max_temperature"] else None,
        last_reading=last_reading,
    )


# ==================== DELETE READINGS ====================

@router.delete("/temperatures", response_model=MessageResponse)
async def delete_temperatures(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    _: str = Depends(verify_api_key),
):
    """Delete temperature readings by date range."""
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
            detail="You must specify at least start_date or end_date to delete",
        )

    result = await db["temperatura"].delete_many(query)

    return MessageResponse(
        message=f"{result.deleted_count} readings deleted", status="ok"
    )
