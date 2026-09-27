from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, cast, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models.gas_hourly_feature import GasHourlyFeature
from app.models.gas_prediction import GasPrediction
from app.models.monitoring_posts import MonitoringPost
from app.schemas.gas_heatmap import (
    GasHeatmapPointOut,
    GasHeatmapResponse,
    GasHeatmapTimelineItemOut,
    GasHeatmapTimelineResponse,
)


def _utc_hour(value: datetime | None = None) -> datetime:
    instant = value or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def get_heatmap_timeline(
    db: Session,
    substance_code: str,
    past_hours: int,
    future_hours: int,
) -> GasHeatmapTimelineResponse:
    current_hour = _utc_hour()
    start = current_hour - timedelta(hours=past_hours)
    end = current_hour + timedelta(hours=future_hours + 1)

    observed = (
        select(
            GasHourlyFeature.bucket_start.label("hour_start"),
            literal("observed").label("data_kind"),
            cast(func.count(), Integer).label("available_points"),
        )
        .join(MonitoringPost, MonitoringPost.id == GasHourlyFeature.monitoring_post_id)
        .where(
            GasHourlyFeature.substance_code == substance_code,
            GasHourlyFeature.bucket_start >= start,
            GasHourlyFeature.bucket_start < current_hour,
            GasHourlyFeature.filtered_hourly_mean.is_not(None),
            MonitoringPost.latitude.is_not(None),
            MonitoringPost.longitude.is_not(None),
        )
        .group_by(GasHourlyFeature.bucket_start)
    )
    forecast = (
        select(
            GasPrediction.target_start.label("hour_start"),
            literal("forecast").label("data_kind"),
            cast(func.count(), Integer).label("available_points"),
        )
        .join(MonitoringPost, MonitoringPost.id == GasPrediction.monitoring_post_id)
        .where(
            GasPrediction.substance_code == substance_code,
            GasPrediction.target_start >= current_hour,
            GasPrediction.target_start < end,
            GasPrediction.status == "ready",
            GasPrediction.predicted_value.is_not(None),
            MonitoringPost.latitude.is_not(None),
            MonitoringPost.longitude.is_not(None),
        )
        .group_by(GasPrediction.target_start)
    )
    available = union_all(observed, forecast).subquery()
    rows = db.execute(
        select(
            available.c.hour_start,
            available.c.data_kind,
            available.c.available_points,
        ).order_by(available.c.hour_start)
    ).all()
    return GasHeatmapTimelineResponse(
        substance_code=substance_code,
        current_hour=current_hour,
        items=[
            GasHeatmapTimelineItemOut(
                hour_start=row.hour_start,
                data_kind=row.data_kind,
                available_points=row.available_points,
            )
            for row in rows
        ],
    )


def get_heatmap_frame(
    db: Session,
    substance_code: str,
    hour_start: datetime,
) -> GasHeatmapResponse:
    selected_hour = _utc_hour(hour_start)
    current_hour = _utc_hour()
    is_forecast = selected_hour >= current_hour
    if is_forecast:
        rows = db.execute(
            select(
                GasPrediction.monitoring_post_id,
                MonitoringPost.latitude,
                MonitoringPost.longitude,
                GasPrediction.predicted_value.label("value"),
                GasPrediction.lower_bound,
                GasPrediction.upper_bound,
                GasPrediction.generated_at,
            )
            .join(MonitoringPost, MonitoringPost.id == GasPrediction.monitoring_post_id)
            .where(
                GasPrediction.substance_code == substance_code,
                GasPrediction.target_start == selected_hour,
                GasPrediction.status == "ready",
                GasPrediction.predicted_value.is_not(None),
                MonitoringPost.latitude.is_not(None),
                MonitoringPost.longitude.is_not(None),
            )
            .order_by(MonitoringPost.id)
        ).all()
        generated_at = max((row.generated_at for row in rows), default=None)
        data_kind = "forecast" if rows else "unavailable"
    else:
        rows = db.execute(
            select(
                GasHourlyFeature.monitoring_post_id,
                MonitoringPost.latitude,
                MonitoringPost.longitude,
                GasHourlyFeature.filtered_hourly_mean.label("value"),
            )
            .join(MonitoringPost, MonitoringPost.id == GasHourlyFeature.monitoring_post_id)
            .where(
                GasHourlyFeature.substance_code == substance_code,
                GasHourlyFeature.bucket_start == selected_hour,
                GasHourlyFeature.filtered_hourly_mean.is_not(None),
                MonitoringPost.latitude.is_not(None),
                MonitoringPost.longitude.is_not(None),
            )
            .order_by(MonitoringPost.id)
        ).all()
        generated_at = None
        data_kind = "observed" if rows else "unavailable"

    return GasHeatmapResponse(
        substance_code=substance_code,
        hour_start=selected_hour,
        hour_end=selected_hour + timedelta(hours=1),
        data_kind=data_kind,
        generated_at=generated_at,
        points=[
            GasHeatmapPointOut(
                monitoring_post_id=row.monitoring_post_id,
                latitude=row.latitude,
                longitude=row.longitude,
                value=row.value,
                lower_bound=row.lower_bound if is_forecast else None,
                upper_bound=row.upper_bound if is_forecast else None,
            )
            for row in rows
        ],
    )
