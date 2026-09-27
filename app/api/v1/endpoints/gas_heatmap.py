from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.gas_heatmap import GasHeatmapResponse, GasHeatmapTimelineResponse
from app.services.gas_heatmap import get_heatmap_frame, get_heatmap_timeline


router = APIRouter(prefix="/gases", tags=["gases"])


@router.get("/heatmap/timeline", response_model=GasHeatmapTimelineResponse)
def gas_heatmap_timeline(
    substance_code: str = Query(..., min_length=1, max_length=20),
    past_hours: int = Query(168, ge=1, le=24 * 366),
    future_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> GasHeatmapTimelineResponse:
    return get_heatmap_timeline(db, substance_code, past_hours, future_hours)


@router.get("/heatmap", response_model=GasHeatmapResponse)
def gas_heatmap(
    substance_code: str = Query(..., min_length=1, max_length=20),
    hour_start: datetime = Query(...),
    db: Session = Depends(get_db),
) -> GasHeatmapResponse:
    return get_heatmap_frame(db, substance_code, hour_start)
