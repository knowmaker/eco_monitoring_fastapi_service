from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_state import DeviceState
from app.models.plc_state import PlcState
from app.schemas.device_state import DeviceStateAvailableOut, DeviceStateAvailableResponse


router = APIRouter(prefix="/device_state", tags=["device_state"])


@router.get("/available", response_model=DeviceStateAvailableResponse)
def get_available_devices(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> DeviceStateAvailableResponse:
    is_device_available = case((DeviceState.ping == "BAD", False), else_=True)
    device_priority = case((DeviceState.ping == "BAD", 1), else_=0)

    devices_ranked_subquery = (
        select(
            DeviceState.device_type.label("device_type"),
            DeviceState.device_name.label("device_name"),
            func.bool_or(is_device_available).over(partition_by=DeviceState.device_type).label("has_available"),
            func.row_number()
            .over(
                partition_by=DeviceState.device_type,
                order_by=(device_priority, PlcState.plc_timestamp_ms.desc(), DeviceState.id.desc()),
            )
            .label("rn"),
        )
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(PlcState.monitoring_post_id == monitoring_post_id)
        .subquery()
    )

    rows = db.execute(
        select(devices_ranked_subquery.c.device_type, devices_ranked_subquery.c.device_name)
        .where(
            devices_ranked_subquery.c.rn == 1,
            devices_ranked_subquery.c.has_available.is_(True),
        )
        .order_by(devices_ranked_subquery.c.device_type.asc())
    ).all()

    return DeviceStateAvailableResponse(
        devices=[DeviceStateAvailableOut(device_type=row[0], device_name=row[1]) for row in rows]
    )
