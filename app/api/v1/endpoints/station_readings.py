from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.station_readings import StationLatestResponse
from app.services.station_readings import get_latest_readings


router = APIRouter(prefix="/station-readings", tags=["station-readings"])


@router.get("/latest", response_model=StationLatestResponse)
def get_station_latest_readings(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> StationLatestResponse:
    return get_latest_readings(db, monitoring_post_id)
