from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_posts import MonitoringPost
from app.schemas.monitoring_posts import (
    MonitoringPostAdminOut,
    MonitoringPostOut,
    MonitoringPostsAdminResponse,
    MonitoringPostsResponse,
    MonitoringPostUpdate,
)


def get_confirmed_posts(db: Session) -> MonitoringPostsResponse:
    rows = db.scalars(
        select(MonitoringPost)
        .where(MonitoringPost.is_confirmed.is_(True))
        .order_by(MonitoringPost.serial.asc())
    ).all()
    return MonitoringPostsResponse(monitoring_posts=[_post_out(row) for row in rows])


def get_all_posts_admin(db: Session) -> MonitoringPostsAdminResponse:
    rows = db.scalars(select(MonitoringPost).order_by(MonitoringPost.serial.asc())).all()
    return MonitoringPostsAdminResponse(monitoring_posts=[_post_admin_out(row) for row in rows])


def update_post_admin(db: Session, monitoring_post_id: int, payload: MonitoringPostUpdate) -> MonitoringPostAdminOut:
    post = db.get(MonitoringPost, monitoring_post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Станция не найдена.")

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        post.name = _clean_optional_text(changes["name"])
    if "post_type" in changes and changes["post_type"] is not None:
        post.post_type = changes["post_type"]
    if "latitude" in changes:
        post.latitude = changes["latitude"]
    if "longitude" in changes:
        post.longitude = changes["longitude"]
    if "notes" in changes:
        post.notes = _clean_optional_text(changes["notes"])
    if "is_confirmed" in changes and changes["is_confirmed"] is not None:
        post.is_confirmed = changes["is_confirmed"]

    _validate_confirmed_post(post)
    db.commit()
    db.refresh(post)
    return _post_admin_out(post)


def _post_out(row: MonitoringPost) -> MonitoringPostOut:
    return MonitoringPostOut(
        id=row.id,
        serial=row.serial,
        name=row.name,
        post_type=row.post_type,
        latitude=row.latitude,
        longitude=row.longitude,
        is_confirmed=row.is_confirmed,
    )


def _post_admin_out(row: MonitoringPost) -> MonitoringPostAdminOut:
    return MonitoringPostAdminOut(
        id=row.id,
        serial=row.serial,
        name=row.name,
        post_type=row.post_type,
        latitude=row.latitude,
        longitude=row.longitude,
        is_confirmed=row.is_confirmed,
        notes=row.notes,
    )


def _validate_confirmed_post(post: MonitoringPost) -> None:
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


def _clean_optional_text(value: str | None) -> str | None:
    return value.strip() if value else None
