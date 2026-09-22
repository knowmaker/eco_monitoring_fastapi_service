from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.monitoring_posts import MonitoringPost
from app.schemas.monitoring_posts import (
    MonitoringPostAdminOut,
    MonitoringPostTransfer,
    MonitoringPostTransferResponse,
    MonitoringPostOut,
    MonitoringPostsAdminResponse,
    MonitoringPostsResponse,
    MonitoringPostUpdate,
)

SAME_LOCATION_DISTANCE_METERS = 10.0
EARTH_RADIUS_METERS = 6_371_008.8


def get_confirmed_posts(db: Session) -> MonitoringPostsResponse:
    rows = db.scalars(
        select(MonitoringPost)
        .where(MonitoringPost.is_confirmed.is_(True))
        .order_by(*_post_ordering())
    ).all()
    return MonitoringPostsResponse(monitoring_posts=[_post_out(row) for row in rows])


def get_all_posts_admin(db: Session) -> MonitoringPostsAdminResponse:
    rows = db.scalars(select(MonitoringPost).order_by(*_post_ordering())).all()
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


def transfer_post_admin(
    db: Session,
    monitoring_post_id: int,
    payload: MonitoringPostTransfer,
) -> MonitoringPostTransferResponse:
    current_post = db.get(MonitoringPost, monitoring_post_id)
    if current_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Станция не найдена.")
    if current_post.active_to is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Перенос доступен только для активной станции.",
        )
    if _is_same_location(current_post, payload.latitude, payload.longitude):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Новые координаты совпадают с текущим местом. Для уточнения координат используйте редактирование.",
        )

    transfer_at = datetime.now(timezone.utc)
    destination_post = _find_previous_location(
        db,
        serial=current_post.serial,
        latitude=payload.latitude,
        longitude=payload.longitude,
        exclude_post_id=current_post.id,
    )

    active_posts = db.scalars(
        select(MonitoringPost).where(
            MonitoringPost.serial == current_post.serial,
            MonitoringPost.active_to.is_(None),
        )
    ).all()
    for active_post in active_posts:
        active_post.active_to = transfer_at
    db.flush()

    reused_existing = destination_post is not None
    if destination_post is None:
        destination_post = MonitoringPost(
            serial=current_post.serial,
            active_from=transfer_at,
        )
        db.add(destination_post)
    else:
        destination_post.active_from = transfer_at

    destination_post.active_to = None
    _apply_transfer_payload(destination_post, payload)
    _validate_confirmed_post(destination_post)

    db.commit()
    db.refresh(destination_post)
    return MonitoringPostTransferResponse(
        monitoring_post=_post_admin_out(destination_post),
        reused_existing=reused_existing,
    )


def _post_out(row: MonitoringPost) -> MonitoringPostOut:
    return MonitoringPostOut(
        id=row.id,
        serial=row.serial,
        name=row.name,
        post_type=row.post_type,
        latitude=row.latitude,
        longitude=row.longitude,
        is_confirmed=row.is_confirmed,
        active_from=row.active_from,
        active_to=row.active_to,
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
        active_from=row.active_from,
        active_to=row.active_to,
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


def _apply_transfer_payload(post: MonitoringPost, payload: MonitoringPostTransfer) -> None:
    post.name = _clean_optional_text(payload.name)
    post.post_type = payload.post_type
    post.latitude = payload.latitude
    post.longitude = payload.longitude
    post.notes = _clean_optional_text(payload.notes)
    post.is_confirmed = payload.is_confirmed


def _find_previous_location(
    db: Session,
    *,
    serial: str,
    latitude: float,
    longitude: float,
    exclude_post_id: int,
) -> MonitoringPost | None:
    candidates = db.scalars(
        select(MonitoringPost).where(
            MonitoringPost.serial == serial,
            MonitoringPost.id != exclude_post_id,
            MonitoringPost.latitude.is_not(None),
            MonitoringPost.longitude.is_not(None),
        )
    ).all()

    closest_post: MonitoringPost | None = None
    closest_distance = SAME_LOCATION_DISTANCE_METERS
    for candidate in candidates:
        distance = _distance_meters(latitude, longitude, candidate.latitude, candidate.longitude)
        if distance <= closest_distance:
            closest_distance = distance
            closest_post = candidate
    return closest_post


def _is_same_location(post: MonitoringPost, latitude: float, longitude: float) -> bool:
    if post.latitude is None or post.longitude is None:
        return False
    return _distance_meters(latitude, longitude, post.latitude, post.longitude) <= SAME_LOCATION_DISTANCE_METERS


def _distance_meters(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float | None,
    longitude_b: float | None,
) -> float:
    if latitude_b is None or longitude_b is None:
        return float("inf")

    delta_latitude = radians(latitude_b - latitude_a)
    delta_longitude = radians(longitude_b - longitude_a)
    lat_a = radians(latitude_a)
    lat_b = radians(latitude_b)
    value = sin(delta_latitude / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_longitude / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(value))


def _post_ordering():
    empty_name_order = case((func.nullif(func.trim(MonitoringPost.name), "").is_(None), 1), else_=0)
    return (
        MonitoringPost.active_to.asc().nulls_first(),
        empty_name_order.asc(),
        func.lower(MonitoringPost.name).asc(),
        MonitoringPost.serial.asc(),
    )
