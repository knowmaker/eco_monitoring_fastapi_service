from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.monitoring_posts import MonitoringPost
from app.schemas.monitoring_posts import MonitoringPostOut, MonitoringPostsResponse


router = APIRouter(prefix="/monitoring_posts", tags=["monitoring_posts"])


@router.get("", response_model=MonitoringPostsResponse)
def get_monitoring_posts(
    db: Session = Depends(get_db),
) -> MonitoringPostsResponse:
    rows = db.scalars(select(MonitoringPost)).all()
    monitoring_posts = [
        MonitoringPostOut(
            id=row.id,
            serial=row.serial,
            latitude=row.latitude,
            longitude=row.longitude,
            is_stationary=row.is_stationary,
        )
        for row in rows
    ]
    return MonitoringPostsResponse(monitoring_posts=monitoring_posts)
