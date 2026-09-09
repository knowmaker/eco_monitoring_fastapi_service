from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.raw_mqtt_payload import RawMqttPayloadResponse
from app.services.raw_mqtt_payload import get_raw_payloads


router = APIRouter(prefix="/raw-mqtt-payload", tags=["raw-mqtt-payload"])


@router.get("/admin", response_model=RawMqttPayloadResponse)
def get_raw_mqtt_payload_admin(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> RawMqttPayloadResponse:
    return get_raw_payloads(db, monitoring_post_id, target_date, limit)
