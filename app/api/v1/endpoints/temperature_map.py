from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.temperature_map import TemperatureMapResponse
from app.services.temperature_map import get_temperature_map


router = APIRouter(prefix="/temperature-map", tags=["temperature-map"])


@router.get("", response_model=TemperatureMapResponse)
def get_temperature_map_state(
    hour_start: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> TemperatureMapResponse:
    return get_temperature_map(db, hour_start)
