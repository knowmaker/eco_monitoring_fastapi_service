from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.mosecom import MOSECOM_DUST_CODES, MOSECOM_GAS_CODES
from app.models.device_state import DeviceState
from app.models.monitoring_posts import MonitoringPost
from app.models.mosecom_hourly_reading import MosecomHourlyReading
from app.models.plc_state import PlcState
from app.schemas.device_state import DeviceStateAvailableOut, DeviceStateAvailableResponse


def get_available_devices(db: Session, monitoring_post_id: int) -> DeviceStateAvailableResponse:
    post = db.get(MonitoringPost, monitoring_post_id)
    if post is not None and post.source == "mosecom":
        substance_codes = set(
            db.scalars(
                select(MosecomHourlyReading.substance_code)
                .where(MosecomHourlyReading.monitoring_post_id == monitoring_post_id)
                .distinct()
            ).all()
        )
        devices = []
        if substance_codes.intersection(MOSECOM_GAS_CODES):
            devices.append(DeviceStateAvailableOut(device_type="gas", device_name="Мосэкомониторинг"))
        if substance_codes.intersection(MOSECOM_DUST_CODES):
            devices.append(DeviceStateAvailableOut(device_type="dust", device_name="Мосэкомониторинг"))
        return DeviceStateAvailableResponse(devices=devices)

    has_device_name = func.nullif(func.trim(DeviceState.device_name), "").is_not(None)
    device_types = db.execute(
        select(DeviceState.device_type)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            DeviceState.ping == "OK",
        )
        .group_by(DeviceState.device_type)
        .order_by(DeviceState.device_type.asc())
    ).scalars().all()

    devices = [
        DeviceStateAvailableOut(
            device_type=device_type,
            device_name=_latest_device_name(db, monitoring_post_id, device_type, has_device_name),
        )
        for device_type in device_types
    ]
    return DeviceStateAvailableResponse(devices=devices)


def _latest_device_name(db: Session, monitoring_post_id: int, device_type: str, has_device_name: object) -> str | None:
    return db.scalar(
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
