from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.concentration_frame import load_frame, value_at
from app.core.config import settings
from app.models.gas_concentration_frame import GasConcentrationFrame
from app.models.pollutant_limit import PollutantLimit
from app.schemas.concentration_map import (
    ConcentrationMapBoundsOut,
    ConcentrationMapResponse,
    ConcentrationMapTimelineItemOut,
    ConcentrationMapTimelineResponse,
    ConcentrationMapValueResponse,
)


def _utc_hour(value: datetime | None = None) -> datetime:
    instant = value or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _data_kind(hour_start: datetime) -> str:
    return "forecast" if hour_start >= _utc_hour() else "observed"


def _select_frame(
    db: Session,
    substance_code: str,
    hour_start: datetime,
) -> GasConcentrationFrame | None:
    return db.scalar(
        select(GasConcentrationFrame).where(
            GasConcentrationFrame.substance_code == substance_code,
            GasConcentrationFrame.hour_start == hour_start,
            GasConcentrationFrame.data_kind == _data_kind(hour_start),
        )
    )


def get_concentration_map_timeline(
    db: Session,
    substance_code: str,
    past_hours: int,
    future_hours: int,
) -> ConcentrationMapTimelineResponse:
    current_hour = _utc_hour()
    start = current_hour - timedelta(hours=past_hours)
    end = current_hour + timedelta(hours=future_hours + 1)
    rows = db.scalars(
        select(GasConcentrationFrame)
        .where(
            GasConcentrationFrame.substance_code == substance_code,
            GasConcentrationFrame.hour_start >= start,
            GasConcentrationFrame.hour_start < end,
            or_(
                and_(
                    GasConcentrationFrame.hour_start < current_hour,
                    GasConcentrationFrame.data_kind == "observed",
                ),
                and_(
                    GasConcentrationFrame.hour_start >= current_hour,
                    GasConcentrationFrame.data_kind == "forecast",
                ),
            ),
        )
        .order_by(GasConcentrationFrame.hour_start)
    ).all()
    return ConcentrationMapTimelineResponse(
        substance_code=substance_code,
        current_hour=current_hour,
        items=[
            ConcentrationMapTimelineItemOut(
                hour_start=row.hour_start,
                data_kind=row.data_kind,
                cell_count=row.cell_count,
            )
            for row in rows
        ],
    )


def get_concentration_map_frame(
    db: Session,
    substance_code: str,
    hour_start: datetime,
) -> ConcentrationMapResponse:
    selected_hour = _utc_hour(hour_start)
    frame = _select_frame(db, substance_code, selected_hour)
    pdk_max_once = db.scalar(
        select(PollutantLimit.pdk_max_once).where(
            PollutantLimit.pollutant_code == substance_code.upper()
        )
    )
    if frame is None:
        return ConcentrationMapResponse(
            substance_code=substance_code,
            pdk_max_once=pdk_max_once,
            hour_start=selected_hour,
            hour_end=selected_hour + timedelta(hours=1),
            data_kind="unavailable",
        )

    tile_url = (
        f"{settings.API_V1_PREFIX}/concentration-map/tiles/"
        f"{frame.id}/{frame.content_sha256}/{{z}}/{{x}}/{{y}}.png"
    )
    return ConcentrationMapResponse(
        substance_code=substance_code,
        pdk_max_once=pdk_max_once,
        hour_start=selected_hour,
        hour_end=selected_hour + timedelta(hours=1),
        data_kind=frame.data_kind,
        generated_at=frame.generated_at,
        source_station_count=frame.source_station_count,
        wind_speed=frame.wind_speed,
        wind_direction=frame.wind_direction,
        cell_count=frame.cell_count,
        cell_size_meters=frame.cell_size_meters,
        value_min=frame.value_min,
        value_max=frame.value_max,
        bounds=ConcentrationMapBoundsOut(
            south=frame.south,
            west=frame.west,
            north=frame.north,
            east=frame.east,
        ),
        tile_url=tile_url,
    )


def get_concentration_map_value(
    db: Session,
    substance_code: str,
    hour_start: datetime,
    latitude: float,
    longitude: float,
) -> ConcentrationMapValueResponse | None:
    selected_hour = _utc_hour(hour_start)
    frame = _select_frame(db, substance_code, selected_hour)
    if frame is None:
        return None
    data = load_frame(frame.id, frame.content_sha256)
    return ConcentrationMapValueResponse(
        substance_code=substance_code,
        hour_start=selected_hour,
        data_kind=frame.data_kind,
        latitude=latitude,
        longitude=longitude,
        value=value_at(data, latitude, longitude),
    )
