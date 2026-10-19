from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.concentration_frame import load_frame, value_at
from app.core.config import settings
from app.models.gas_concentration_frame import GasConcentrationFrame
from app.models.gas_hourly_feature import GasHourlyFeature
from app.models.gas_prediction import GasPrediction
from app.models.pollutant_limit import PollutantLimit
from app.schemas.concentration_map import (
    ConcentrationMapBoundsOut,
    ConcentrationMapResponse,
    ConcentrationMapSubstancesResponse,
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
    return "forecast" if hour_start >= _utc_hour() else "analysis"


def _source_station_ids(
    db: Session,
    frame: GasConcentrationFrame,
) -> list[int]:
    source_analysis_generated = None
    if frame.data_kind == "forecast" and frame.hour_start == _utc_hour():
        source_analysis_generated = db.scalar(
            select(GasConcentrationFrame.generated_at).where(
                GasConcentrationFrame.substance_code == frame.substance_code,
                GasConcentrationFrame.hour_start == frame.hour_start - timedelta(hours=1),
                GasConcentrationFrame.data_kind == "analysis",
            )
        )
    is_nowcast = (
        source_analysis_generated is not None
        and frame.generated_at >= source_analysis_generated
    )
    if frame.data_kind == "analysis" or is_nowcast:
        station_id_column = GasHourlyFeature.monitoring_post_id
        statement = select(station_id_column).where(
            GasHourlyFeature.substance_code == frame.substance_code,
            GasHourlyFeature.bucket_start == (
                frame.hour_start if frame.data_kind == "analysis"
                else frame.hour_start - timedelta(hours=1)
            ),
            GasHourlyFeature.filtered_hourly_mean.is_not(None),
        )
        return list(db.scalars(statement.order_by(station_id_column)).all())
    return list(db.scalars(
        select(GasPrediction.monitoring_post_id)
        .join(
            GasHourlyFeature,
            and_(
                GasHourlyFeature.monitoring_post_id == GasPrediction.monitoring_post_id,
                GasHourlyFeature.substance_code == GasPrediction.substance_code,
                GasHourlyFeature.bucket_start
                == GasPrediction.data_cutoff - timedelta(hours=1),
            ),
        )
        .where(
            GasPrediction.substance_code == frame.substance_code,
            GasPrediction.target_start == frame.hour_start,
            GasPrediction.status == "ready",
            GasPrediction.predicted_value.is_not(None),
            GasHourlyFeature.filtered_hourly_mean.is_not(None),
        )
        .order_by(GasPrediction.monitoring_post_id)
    ).all())


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
                    GasConcentrationFrame.data_kind == "analysis",
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

    monitoring_post_ids = _source_station_ids(db, frame)

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
        monitoring_post_ids=monitoring_post_ids,
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


def get_concentration_map_substances(db: Session) -> ConcentrationMapSubstancesResponse:
    items = db.scalars(
        select(GasConcentrationFrame.substance_code)
        .where(GasConcentrationFrame.data_kind == "forecast")
        .distinct()
        .order_by(GasConcentrationFrame.substance_code)
    ).all()
    return ConcentrationMapSubstancesResponse(items=list(items))
