from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.plc_state import PlcState
from app.models.raw_mqtt_payload import RawMqttPayload
from app.models.user import User
from app.schemas.raw_mqtt_payload import RawMqttPayloadRecordOut, RawMqttPayloadResponse


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/raw_mqtt_payload", tags=["raw_mqtt_payload"])


def local_day_bounds_ms(day: date) -> tuple[int, int]:
    timezone = ZoneInfo(APP_TIMEZONE)
    start = datetime.combine(day, time.min, tzinfo=timezone)
    end = start + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


@router.get("/admin", response_model=RawMqttPayloadResponse)
def get_raw_mqtt_payload_admin(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> RawMqttPayloadResponse:
    query = (
        select(RawMqttPayload.payload)
        .join(PlcState, PlcState.id == RawMqttPayload.plc_state_id)
        .where(PlcState.monitoring_post_id == monitoring_post_id)
        .order_by(PlcState.plc_timestamp_ms.desc(), PlcState.id.desc())
    )

    if target_date is not None:
        start_ms, end_ms = local_day_bounds_ms(target_date)
        query = query.where(
            PlcState.plc_timestamp_ms >= start_ms,
            PlcState.plc_timestamp_ms < end_ms,
        )

    rows = db.execute(query.limit(limit)).scalars().all()
    records = [RawMqttPayloadRecordOut(packet=payload) for payload in rows]

    return RawMqttPayloadResponse(
        monitoring_post_id=monitoring_post_id,
        date=target_date.isoformat() if target_date else None,
        limit=limit,
        records=records,
    )
