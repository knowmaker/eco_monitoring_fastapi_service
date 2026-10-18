from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.concentration_map import (
    ConcentrationMapResponse,
    ConcentrationMapTimelineResponse,
)
from app.services.concentration_map import (
    get_concentration_map_frame,
    get_concentration_map_timeline,
)


router = APIRouter(prefix="/concentration-map", tags=["concentration-map"])


@router.get("/timeline", response_model=ConcentrationMapTimelineResponse)
def concentration_map_timeline(
    substance_code: str = Query(..., min_length=1, max_length=20),
    past_hours: int = Query(168, ge=1, le=24 * 366),
    future_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> ConcentrationMapTimelineResponse:
    return get_concentration_map_timeline(db, substance_code, past_hours, future_hours)


@router.get("", response_model=ConcentrationMapResponse)
def concentration_map(
    substance_code: str = Query(..., min_length=1, max_length=20),
    hour_start: datetime = Query(...),
    db: Session = Depends(get_db),
) -> ConcentrationMapResponse:
    return get_concentration_map_frame(db, substance_code, hour_start)
