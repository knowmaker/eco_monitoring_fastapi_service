from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.monitoring_posts import (
    MonitoringPostAdminOut,
    MonitoringPostsAdminResponse,
    MonitoringPostsResponse,
    MonitoringPostUpdate,
)
from app.services.monitoring_posts import get_all_posts_admin, get_confirmed_posts, update_post_admin


router = APIRouter(prefix="/monitoring-posts", tags=["monitoring-posts"])


@router.get("", response_model=MonitoringPostsResponse)
def get_monitoring_posts(db: Session = Depends(get_db)) -> MonitoringPostsResponse:
    return get_confirmed_posts(db)


@router.get("/admin", response_model=MonitoringPostsAdminResponse)
def get_monitoring_posts_admin(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MonitoringPostsAdminResponse:
    return get_all_posts_admin(db)


@router.patch("/{monitoring_post_id}", response_model=MonitoringPostAdminOut)
def update_monitoring_post(
    monitoring_post_id: int,
    payload: MonitoringPostUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MonitoringPostAdminOut:
    return update_post_admin(db, monitoring_post_id, payload)
