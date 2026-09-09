from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.station_readings import StationLatestHourlyResponse
from app.services.station_readings import get_latest_hourly_readings


router = APIRouter(prefix="/station-readings", tags=["station-readings"])


@router.get("/latest-hourly", response_model=StationLatestHourlyResponse)
def get_station_latest_hourly_readings(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> StationLatestHourlyResponse:
    return get_latest_hourly_readings(db, monitoring_post_id)
