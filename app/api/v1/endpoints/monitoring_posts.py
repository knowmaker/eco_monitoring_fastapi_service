from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.monitoring_posts import MonitoringPost
from app.models.user import User
from app.schemas.monitoring_posts import (
    MonitoringPostOut,
    MonitoringPostsResponse,
    MonitoringPostUpdate,
)


router = APIRouter(prefix="/monitoring_posts", tags=["monitoring_posts"])


def to_post_out(row: MonitoringPost) -> MonitoringPostOut:
    return MonitoringPostOut(
        id=row.id,
        serial=row.serial,
        name=row.name,
        post_type=row.post_type,
        latitude=row.latitude,
        longitude=row.longitude,
        is_confirmed=row.is_confirmed,
    )


def validate_confirmed_post(post: MonitoringPost) -> None:
    if not post.is_confirmed:
        return
    if not post.name or not post.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Для подтверждения станции укажите название.",
        )
    if post.post_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Для подтверждения станции выберите тип поста.",
        )
    if post.latitude is None or post.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Для подтверждения станции укажите координаты.",
        )


@router.get("", response_model=MonitoringPostsResponse)
def get_monitoring_posts(
    db: Session = Depends(get_db),
) -> MonitoringPostsResponse:
    rows = db.scalars(
        select(MonitoringPost)
        .where(MonitoringPost.is_confirmed.is_(True))
        .order_by(MonitoringPost.serial.asc())
    ).all()
    monitoring_posts = [to_post_out(row) for row in rows]
    return MonitoringPostsResponse(monitoring_posts=monitoring_posts)


@router.get("/admin", response_model=MonitoringPostsResponse)
def get_monitoring_posts_admin(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MonitoringPostsResponse:
    rows = db.scalars(select(MonitoringPost).order_by(MonitoringPost.serial.asc())).all()
    monitoring_posts = [to_post_out(row) for row in rows]
    return MonitoringPostsResponse(monitoring_posts=monitoring_posts)


@router.patch("/{monitoring_post_id}", response_model=MonitoringPostOut)
def update_monitoring_post(
    monitoring_post_id: int,
    payload: MonitoringPostUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> MonitoringPostOut:
    post = db.get(MonitoringPost, monitoring_post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Станция не найдена.")

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        post.name = changes["name"].strip() if changes["name"] else None
    if "post_type" in changes and changes["post_type"] is not None:
        post.post_type = changes["post_type"]
    if "latitude" in changes:
        post.latitude = changes["latitude"]
    if "longitude" in changes:
        post.longitude = changes["longitude"]
    if "is_confirmed" in changes and changes["is_confirmed"] is not None:
        post.is_confirmed = changes["is_confirmed"]

    validate_confirmed_post(post)
    db.commit()
    db.refresh(post)
    return to_post_out(post)
