from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.values import to_float
from app.models.cagg_dust_hourly import CaggDustHourly
from app.models.cagg_gas_hourly import CaggGasHourly
from app.models.cagg_ivtm_hourly import CaggIvtmHourly
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.models.cagg_profile_inversion_hourly import CaggProfileInversionHourly
from app.models.cagg_profile_levels_hourly import CaggProfileLevelsHourly
from app.models.pollutant_limit import PollutantLimit
from app.schemas.station_readings import (
    LatestDustHourlyOut,
    LatestGasHourlyOut,
    LatestGasSubstanceOut,
    LatestIvtmHourlyOut,
    LatestMeteoHourlyOut,
    LatestProfileHourlyOut,
    LatestProfileLevelOut,
    PollutantLimitOut,
    StationLatestHourlyResponse,
)


def get_latest_hourly_readings(db: Session, monitoring_post_id: int) -> StationLatestHourlyResponse:
    limits_by_code = _pollutant_limits_by_code(db)
    buckets = {
        "gas": _latest_bucket(db, CaggGasHourly, monitoring_post_id, CaggGasHourly.value_avg),
        "dust": _latest_bucket(
            db,
            CaggDustHourly,
            monitoring_post_id,
            CaggDustHourly.pm1_avg,
            CaggDustHourly.pm2_avg,
            CaggDustHourly.pm10_avg,
            CaggDustHourly.tsp_avg,
        ),
        "meteo": _latest_bucket(
            db,
            CaggMeteoHourly,
            monitoring_post_id,
            CaggMeteoHourly.atm_press_avg,
            CaggMeteoHourly.air_temp_avg,
            CaggMeteoHourly.air_hum_avg,
            CaggMeteoHourly.hor_win_dir_avg,
            CaggMeteoHourly.hor_win_spd_avg,
        ),
        "ivtm": _latest_bucket(
            db,
            CaggIvtmHourly,
            monitoring_post_id,
            CaggIvtmHourly.sensor_ivtm_hum_avg,
            CaggIvtmHourly.sensor_ivtm_temp_avg,
        ),
        "profile": _latest_bucket(
            db,
            CaggProfileLevelsHourly,
            monitoring_post_id,
            CaggProfileLevelsHourly.temperature_avg,
        ),
    }
    latest_bucket_ms = max((bucket for bucket in buckets.values() if bucket is not None), default=None)

    if latest_bucket_ms is None:
        return StationLatestHourlyResponse(
            monitoring_post_id=monitoring_post_id,
            bucket_ms=None,
            gas=None,
            dust=None,
            meteo=None,
            ivtm=None,
            profile=None,
        )

    return StationLatestHourlyResponse(
        monitoring_post_id=monitoring_post_id,
        bucket_ms=latest_bucket_ms,
        gas=_latest_gas(db, monitoring_post_id, buckets["gas"], limits_by_code),
        dust=_latest_dust(db, monitoring_post_id, buckets["dust"], limits_by_code),
        meteo=_latest_meteo(db, monitoring_post_id, buckets["meteo"]),
        ivtm=_latest_ivtm(db, monitoring_post_id, buckets["ivtm"]),
        profile=_latest_profile(db, monitoring_post_id, buckets["profile"]),
    )


def _pollutant_limits_by_code(db: Session) -> dict[str, PollutantLimit]:
    limit_rows = db.execute(select(PollutantLimit)).scalars().all()
    return {row.pollutant_code.upper(): row for row in limit_rows}


def _limit_out(limit: PollutantLimit | None) -> PollutantLimitOut | None:
    if limit is None:
        return None
    return PollutantLimitOut(
        pollutant_code=limit.pollutant_code,
        pdk_max_once=to_float(limit.pdk_max_once),
        pdk_daily=to_float(limit.pdk_daily),
        pdk_annual=to_float(limit.pdk_annual),
        comparison_pdk=to_float(limit.pdk_max_once),
        comparison_kind="max_once",
    )


def _latest_bucket(db: Session, model: type, monitoring_post_id: int, *value_columns: object) -> int | None:
    conditions = [model.monitoring_post_id == monitoring_post_id]
    if value_columns:
        conditions.append(or_(*(column.is_not(None) for column in value_columns)))
    return db.scalar(select(func.max(model.bucket_ms)).where(*conditions))


def _latest_gas(
    db: Session,
    monitoring_post_id: int,
    bucket_ms: int | None,
    limits_by_code: dict[str, PollutantLimit],
) -> LatestGasHourlyOut | None:
    if bucket_ms is None:
        return None

    rows = db.execute(
        select(CaggGasHourly)
        .where(
            CaggGasHourly.monitoring_post_id == monitoring_post_id,
            CaggGasHourly.bucket_ms == bucket_ms,
            CaggGasHourly.value_avg.is_not(None),
        )
        .order_by(CaggGasHourly.substance_code.asc())
    ).scalars().all()

    if not rows:
        return None

    return LatestGasHourlyOut(
        bucket_ms=bucket_ms,
        substances=[
            LatestGasSubstanceOut(
                substance_code=row.substance_code,
                value=to_float(row.value_avg),
                limit=_limit_out(limits_by_code.get(row.substance_code.upper())),
            )
            for row in rows
        ],
    )


def _latest_dust(
    db: Session,
    monitoring_post_id: int,
    bucket_ms: int | None,
    limits_by_code: dict[str, PollutantLimit],
) -> LatestDustHourlyOut | None:
    row = _scalar_bucket_row(db, CaggDustHourly, monitoring_post_id, bucket_ms)
    if row is None:
        return None

    return LatestDustHourlyOut(
        bucket_ms=bucket_ms,
        pm1=to_float(row.pm1_avg),
        pm2=to_float(row.pm2_avg),
        pm10=to_float(row.pm10_avg),
        tsp=to_float(row.tsp_avg),
        limits={
            "pm1": _limit_out(limits_by_code.get("PM1")),
            "pm2": _limit_out(limits_by_code.get("PM2.5")),
            "pm10": _limit_out(limits_by_code.get("PM10")),
            "tsp": _limit_out(limits_by_code.get("TSP")),
        },
    )


def _latest_meteo(db: Session, monitoring_post_id: int, bucket_ms: int | None) -> LatestMeteoHourlyOut | None:
    row = _scalar_bucket_row(db, CaggMeteoHourly, monitoring_post_id, bucket_ms)
    if row is None:
        return None

    return LatestMeteoHourlyOut(
        bucket_ms=bucket_ms,
        atm_press=to_float(row.atm_press_avg),
        air_temp=to_float(row.air_temp_avg),
        air_hum=to_float(row.air_hum_avg),
        hor_win_dir=to_float(row.hor_win_dir_avg),
        hor_win_spd=to_float(row.hor_win_spd_avg),
    )


def _latest_ivtm(db: Session, monitoring_post_id: int, bucket_ms: int | None) -> LatestIvtmHourlyOut | None:
    row = _scalar_bucket_row(db, CaggIvtmHourly, monitoring_post_id, bucket_ms)
    if row is None:
        return None

    return LatestIvtmHourlyOut(
        bucket_ms=bucket_ms,
        sensor_ivtm_hum=to_float(row.sensor_ivtm_hum_avg),
        sensor_ivtm_temp=to_float(row.sensor_ivtm_temp_avg),
    )


def _latest_profile(db: Session, monitoring_post_id: int, bucket_ms: int | None) -> LatestProfileHourlyOut | None:
    if bucket_ms is None:
        return None

    level_rows = db.execute(
        select(CaggProfileLevelsHourly)
        .where(
            CaggProfileLevelsHourly.monitoring_post_id == monitoring_post_id,
            CaggProfileLevelsHourly.bucket_ms == bucket_ms,
            CaggProfileLevelsHourly.temperature_avg.is_not(None),
        )
        .order_by(CaggProfileLevelsHourly.height.asc())
    ).scalars().all()

    if not level_rows:
        return None

    inversion_row = db.scalar(
        select(CaggProfileInversionHourly).where(
            CaggProfileInversionHourly.monitoring_post_id == monitoring_post_id,
            CaggProfileInversionHourly.bucket_ms == bucket_ms,
        )
    )

    return LatestProfileHourlyOut(
        bucket_ms=bucket_ms,
        levels=[
            LatestProfileLevelOut(
                height=float(row.height),
                temperature=to_float(row.temperature_avg),
            )
            for row in level_rows
        ],
        inversion_power=to_float(inversion_row.inversion_power_avg) if inversion_row else None,
        inversion_lower=to_float(inversion_row.inversion_lower_avg) if inversion_row else None,
        inversion_upper=to_float(inversion_row.inversion_upper_avg) if inversion_row else None,
        inversion_delta_t=to_float(inversion_row.inversion_delta_t_avg) if inversion_row else None,
    )


def _scalar_bucket_row(db: Session, model: type, monitoring_post_id: int, bucket_ms: int | None):
    if bucket_ms is None:
        return None
    return db.scalar(
        select(model).where(
            model.monitoring_post_id == monitoring_post_id,
            model.bucket_ms == bucket_ms,
        )
    )
