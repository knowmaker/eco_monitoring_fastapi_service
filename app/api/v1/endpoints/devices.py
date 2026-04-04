from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.devices import DeviceInfo, DevicesResponse


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DevicesResponse)
def get_devices(
    db: Session = Depends(get_db),
) -> DevicesResponse:
    rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (serial)
                serial,
                latitude,
                longitude
            FROM plc_state
            WHERE serial IS NOT NULL
            ORDER BY
                serial,
                (latitude IS NULL OR longitude IS NULL),
                plc_timestamp_ms DESC
            """
        )
    ).all()
    devices = [
        DeviceInfo(
            serial=row[0],
            latitude=row[1],
            longitude=row[2],
        )
        for row in rows
    ]
    return DevicesResponse(devices=devices)
