from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import local_day_bounds_ms
from app.models.plc_state import PlcState
from app.models.raw_mqtt_payload import RawMqttPayload
from app.schemas.raw_mqtt_payload import RawMqttPayloadRecordOut, RawMqttPayloadResponse


def get_raw_payloads(
    db: Session,
    monitoring_post_id: int,
    target_date: date | None,
    limit: int,
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
