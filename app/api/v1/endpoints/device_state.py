from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.device_state import DeviceStateAvailableResponse
from app.services.device_state import get_available_devices as get_available_devices_service


router = APIRouter(prefix="/device-state", tags=["device-state"])


@router.get("/available", response_model=DeviceStateAvailableResponse)
def get_available_devices(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> DeviceStateAvailableResponse:
    return get_available_devices_service(db, monitoring_post_id)
