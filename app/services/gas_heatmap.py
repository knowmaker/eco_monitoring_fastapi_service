from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, and_, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.gas_concentration_grid import GasConcentrationGrid
from app.schemas.gas_heatmap import (
    GasHeatmapCellOut,
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
    rows = db.execute(
        select(
            GasConcentrationGrid.hour_start,
            GasConcentrationGrid.data_kind,
            cast(func.count(), Integer).label("available_cells"),
        )
        .where(
            GasConcentrationGrid.substance_code == substance_code,
            GasConcentrationGrid.hour_start >= start,
            GasConcentrationGrid.hour_start < end,
            or_(
                and_(
                    GasConcentrationGrid.hour_start < current_hour,
                    GasConcentrationGrid.data_kind == "observed",
                ),
                and_(
                    GasConcentrationGrid.hour_start >= current_hour,
                    GasConcentrationGrid.data_kind == "forecast",
                ),
            ),
        )
        .group_by(GasConcentrationGrid.hour_start, GasConcentrationGrid.data_kind)
        .order_by(GasConcentrationGrid.hour_start)
    ).all()
    return GasHeatmapTimelineResponse(
        substance_code=substance_code,
        current_hour=current_hour,
        items=[
            GasHeatmapTimelineItemOut(
                hour_start=row.hour_start,
                data_kind=row.data_kind,
                available_cells=row.available_cells,
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
    data_kind = "forecast" if selected_hour >= _utc_hour() else "observed"
    rows = db.execute(
        select(GasConcentrationGrid)
        .where(
            GasConcentrationGrid.substance_code == substance_code,
            GasConcentrationGrid.hour_start == selected_hour,
            GasConcentrationGrid.data_kind == data_kind,
        )
        .order_by(
            GasConcentrationGrid.cluster_id,
            GasConcentrationGrid.grid_y,
            GasConcentrationGrid.grid_x,
        )
    ).scalars().all()
    if not rows:
        data_kind = "unavailable"
    station_counts = {
        row.cluster_id: row.source_station_count
        for row in rows
    }

    return GasHeatmapResponse(
        substance_code=substance_code,
        hour_start=selected_hour,
        hour_end=selected_hour + timedelta(hours=1),
        data_kind=data_kind,
        generated_at=max((row.generated_at for row in rows), default=None),
        source_station_count=sum(station_counts.values()),
        wind_speed=rows[0].wind_speed if rows else None,
        wind_direction=rows[0].wind_direction if rows else None,
        cells=[
            GasHeatmapCellOut(
                latitude=row.latitude,
                longitude=row.longitude,
                south=row.south,
                west=row.west,
                north=row.north,
                east=row.east,
                value=row.value,
                confidence=row.confidence,
                lower_bound=row.lower_bound,
                upper_bound=row.upper_bound,
            )
            for row in rows
        ],
    )
