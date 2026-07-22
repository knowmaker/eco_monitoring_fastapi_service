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
    has_device_name = func.nullif(func.trim(DeviceState.device_name), "").is_not(None)

    device_types = db.execute(
        select(DeviceState.device_type)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(PlcState.monitoring_post_id == monitoring_post_id)
        .group_by(DeviceState.device_type)
        .having(func.bool_or(is_device_available).is_(True))
        .order_by(DeviceState.device_type.asc())
    ).scalars().all()

    devices = []
    for device_type in device_types:
        device_name = db.scalar(
            select(DeviceState.device_name)
            .join(PlcState, PlcState.id == DeviceState.plc_state_id)
            .where(
                PlcState.monitoring_post_id == monitoring_post_id,
                DeviceState.device_type == device_type,
                has_device_name,
            )
            .order_by(PlcState.plc_timestamp_ms.desc(), DeviceState.id.desc())
            .limit(1)
        )
        devices.append(DeviceStateAvailableOut(device_type=device_type, device_name=device_name))

    return DeviceStateAvailableResponse(devices=devices)
