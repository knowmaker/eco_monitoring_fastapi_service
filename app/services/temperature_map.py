from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import APP_ZONEINFO
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.models.cagg_profile_inversion_hourly import CaggProfileInversionHourly
from app.models.cagg_profile_levels_hourly import CaggProfileLevelsHourly
from app.models.monitoring_posts import MonitoringPost
from app.models.mosecom_profile_hourly import MosecomProfileHourly
from app.schemas.temperature_map import (
    TemperatureMapLevelOut,
    TemperatureMapResponse,
    TemperatureMapStationOut,
)
from app.schemas.profile_state import ProfileInversionOut


def _bucket_ms(db: Session, hour_start: datetime | None) -> int:
    if hour_start is not None:
        local_hour = (
            hour_start.replace(tzinfo=APP_ZONEINFO)
            if hour_start.tzinfo is None
            else hour_start.astimezone(APP_ZONEINFO)
        ).replace(minute=0, second=0, microsecond=0)
        return int(local_hour.timestamp() * 1000)

    latest_buckets = (
        db.scalar(
            select(func.max(CaggProfileLevelsHourly.bucket_ms)).where(
                CaggProfileLevelsHourly.temperature_avg.is_not(None)
            )
        ),
        db.scalar(select(func.max(MosecomProfileHourly.bucket_ms))),
        db.scalar(
            select(func.max(CaggMeteoHourly.bucket_ms)).where(CaggMeteoHourly.air_temp_avg.is_not(None))
        ),
    )
    return max(
        (value for value in latest_buckets if value is not None),
        default=int(datetime.now(APP_ZONEINFO).replace(minute=0, second=0, microsecond=0).timestamp() * 1000),
    )


def _station(
    row,
    device_type: str,
    levels: list[TemperatureMapLevelOut] | None = None,
) -> TemperatureMapStationOut:
    return TemperatureMapStationOut(
        monitoring_post_id=row.monitoring_post_id,
        name=row.name,
        serial=row.serial,
        source=row.source,
        device_type=device_type,
        latitude=float(row.latitude),
        longitude=float(row.longitude),
        levels=levels or [],
    )


def get_temperature_map(db: Session, hour_start: datetime | None) -> TemperatureMapResponse:
    bucket_ms = _bucket_ms(db, hour_start)
    station_columns = (
        MonitoringPost.id.label("monitoring_post_id"),
        MonitoringPost.name,
        MonitoringPost.serial,
        MonitoringPost.source,
        MonitoringPost.latitude,
        MonitoringPost.longitude,
    )
    station_filters = (
        MonitoringPost.is_confirmed.is_(True),
        MonitoringPost.latitude.is_not(None),
        MonitoringPost.longitude.is_not(None),
    )
    internal_profile_rows = db.execute(
        select(
            *station_columns,
            CaggProfileLevelsHourly.height,
            CaggProfileLevelsHourly.temperature_avg.label("temperature"),
        )
        .join(MonitoringPost, MonitoringPost.id == CaggProfileLevelsHourly.monitoring_post_id)
        .where(
            CaggProfileLevelsHourly.bucket_ms == bucket_ms,
            CaggProfileLevelsHourly.temperature_avg.is_not(None),
            MonitoringPost.source == "internal",
            *station_filters,
        )
        .order_by(MonitoringPost.id, CaggProfileLevelsHourly.height)
    ).all()
    mosecom_profile_rows = db.execute(
        select(
            *station_columns,
            MosecomProfileHourly.height,
            MosecomProfileHourly.temperature_avg.label("temperature"),
        )
        .join(MonitoringPost, MonitoringPost.id == MosecomProfileHourly.monitoring_post_id)
        .where(
            MosecomProfileHourly.bucket_ms == bucket_ms,
            MonitoringPost.source == "mosecom",
            *station_filters,
        )
        .order_by(MonitoringPost.id, MosecomProfileHourly.height)
    ).all()
    meteo_rows = db.execute(
        select(
            *station_columns,
            CaggMeteoHourly.air_temp_avg.label("temperature"),
        )
        .join(MonitoringPost, MonitoringPost.id == CaggMeteoHourly.monitoring_post_id)
        .where(
            CaggMeteoHourly.bucket_ms == bucket_ms,
            CaggMeteoHourly.air_temp_avg.is_not(None),
            MonitoringPost.source == "internal",
            *station_filters,
        )
        .order_by(MonitoringPost.id)
    ).all()
    inversion_rows = db.execute(
        select(CaggProfileInversionHourly).where(
            CaggProfileInversionHourly.bucket_ms == bucket_ms,
            CaggProfileInversionHourly.inversion_power_avg > 0,
            CaggProfileInversionHourly.inversion_lower_avg.is_not(None),
            CaggProfileInversionHourly.inversion_upper_avg.is_not(None),
        )
    ).scalars()

    stations: dict[int, TemperatureMapStationOut] = {}
    temperatures: list[float] = []
    for row in (*internal_profile_rows, *mosecom_profile_rows):
        temperature = float(row.temperature)
        height = float(row.height)
        station = stations.setdefault(row.monitoring_post_id, _station(row, "profile"))
        station.levels.append(TemperatureMapLevelOut(height=height, temperature=temperature))
        temperatures.append(temperature)

    for row in meteo_rows:
        if row.monitoring_post_id in stations:
            continue
        temperature = float(row.temperature)
        stations[row.monitoring_post_id] = _station(
            row,
            "meteo",
            [TemperatureMapLevelOut(height=0.0, temperature=temperature)],
        )
        temperatures.append(temperature)

    for row in inversion_rows:
        station = stations.get(row.monitoring_post_id)
        if station is None or station.device_type != "profile":
            continue
        station.inversion = ProfileInversionOut(
            power=float(row.inversion_power_avg),
            lower=float(row.inversion_lower_avg),
            upper=float(row.inversion_upper_avg),
            deltaT=float(row.inversion_delta_t_avg) if row.inversion_delta_t_avg is not None else None,
        )

    selected_hour = datetime.fromtimestamp(bucket_ms / 1000, APP_ZONEINFO)
    return TemperatureMapResponse(
        hour_start=selected_hour,
        hour_end=selected_hour + timedelta(hours=1),
        station_count=len(stations),
        min_temperature=min(temperatures, default=None),
        max_temperature=max(temperatures, default=None),
        stations=list(stations.values()),
    )
