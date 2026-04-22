from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.plc_state import PlcState
from app.schemas.plc_state import PlcStateLatestOut, PlcStateLatestResponse


router = APIRouter(prefix="/plc_state", tags=["plc_state"])


@router.get("/latest", response_model=PlcStateLatestResponse)
def get_latest_plc_state(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> PlcStateLatestResponse:
    row = db.scalar(
        select(PlcState)
        .where(PlcState.monitoring_post_id == monitoring_post_id)
        .order_by(PlcState.plc_timestamp_ms.desc(), PlcState.id.desc())
        .limit(1)
    )
    if row is None:
        return PlcStateLatestResponse(plc_state=None)

    return PlcStateLatestResponse(
        plc_state=PlcStateLatestOut(
            id=row.id,
            monitoring_post_id=row.monitoring_post_id,
            plc_timestamp_ms=row.plc_timestamp_ms,
            received_at=row.received_at.isoformat(),
        )
    )
