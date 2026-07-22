from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_dust_hourly import CaggDustHourly
from app.models.cagg_gas_hourly import CaggGasHourly
from app.models.cagg_ivtm_hourly import CaggIvtmHourly
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.models.pollutant_limit import PollutantLimit
from app.schemas.station_readings import (
    LatestDustHourlyOut,
    LatestGasHourlyOut,
    LatestGasSubstanceOut,
    LatestIvtmHourlyOut,
    LatestMeteoHourlyOut,
    PollutantLimitOut,
    StationLatestHourlyResponse,
)


router = APIRouter(prefix="/station_readings", tags=["station_readings"])


def to_float(value: object) -> float | None:
    return float(value) if value is not None else None


def to_limit_out(limit: PollutantLimit | None) -> PollutantLimitOut | None:
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


def get_latest_bucket_ms(db: Session, model: type, monitoring_post_id: int, *value_columns: object) -> int | None:
    conditions = [model.monitoring_post_id == monitoring_post_id]
    if value_columns:
        conditions.append(or_(*(column.is_not(None) for column in value_columns)))
    return db.scalar(select(func.max(model.bucket_ms)).where(*conditions))


@router.get("/latest_hourly", response_model=StationLatestHourlyResponse)
def get_station_latest_hourly_readings(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> StationLatestHourlyResponse:
    limit_rows = db.execute(select(PollutantLimit)).scalars().all()
    limits_by_code = {row.pollutant_code.upper(): row for row in limit_rows}

    gas_bucket_ms = get_latest_bucket_ms(db, CaggGasHourly, monitoring_post_id, CaggGasHourly.value_avg)
    dust_bucket_ms = get_latest_bucket_ms(
        db,
        CaggDustHourly,
        monitoring_post_id,
        CaggDustHourly.pm1_avg,
        CaggDustHourly.pm2_avg,
        CaggDustHourly.pm10_avg,
        CaggDustHourly.tsp_avg,
    )
    meteo_bucket_ms = get_latest_bucket_ms(
        db,
        CaggMeteoHourly,
        monitoring_post_id,
        CaggMeteoHourly.atm_press_avg,
        CaggMeteoHourly.air_temp_avg,
        CaggMeteoHourly.air_hum_avg,
        CaggMeteoHourly.hor_win_dir_avg,
        CaggMeteoHourly.hor_win_spd_avg,
    )
    ivtm_bucket_ms = get_latest_bucket_ms(
        db,
        CaggIvtmHourly,
        monitoring_post_id,
        CaggIvtmHourly.sensor_ivtm_hum_avg,
        CaggIvtmHourly.sensor_ivtm_temp_avg,
    )
    bucket_candidates = [gas_bucket_ms, dust_bucket_ms, meteo_bucket_ms, ivtm_bucket_ms]
    latest_bucket_ms = max((bucket for bucket in bucket_candidates if bucket is not None), default=None)

    if latest_bucket_ms is None:
        return StationLatestHourlyResponse(
            monitoring_post_id=monitoring_post_id,
            bucket_ms=None,
            gas=None,
            dust=None,
            meteo=None,
            ivtm=None,
        )

    gas_rows = (
        db.execute(
            select(CaggGasHourly)
            .where(
                CaggGasHourly.monitoring_post_id == monitoring_post_id,
                CaggGasHourly.bucket_ms == gas_bucket_ms,
                CaggGasHourly.value_avg.is_not(None),
            )
            .order_by(CaggGasHourly.substance_code.asc())
        ).scalars().all()
        if gas_bucket_ms is not None
        else []
    )
    gas = (
        LatestGasHourlyOut(
            bucket_ms=gas_bucket_ms,
            substances=[
                LatestGasSubstanceOut(
                    substance_code=row.substance_code,
                    value=to_float(row.value_avg),
                    limit=to_limit_out(limits_by_code.get(row.substance_code.upper())),
                )
                for row in gas_rows
            ]
        )
        if gas_rows
        else None
    )

    dust_row = (
        db.scalar(
            select(CaggDustHourly).where(
                CaggDustHourly.monitoring_post_id == monitoring_post_id,
                CaggDustHourly.bucket_ms == dust_bucket_ms,
            )
        )
        if dust_bucket_ms is not None
        else None
    )
    dust = (
        LatestDustHourlyOut(
            bucket_ms=dust_bucket_ms,
            pm1=to_float(dust_row.pm1_avg),
            pm2=to_float(dust_row.pm2_avg),
            pm10=to_float(dust_row.pm10_avg),
            tsp=to_float(dust_row.tsp_avg),
            limits={
                "pm1": to_limit_out(limits_by_code.get("PM1")),
                "pm2": to_limit_out(limits_by_code.get("PM2.5")),
                "pm10": to_limit_out(limits_by_code.get("PM10")),
                "tsp": to_limit_out(limits_by_code.get("TSP")),
            },
        )
        if dust_row
        else None
    )

    meteo_row = (
        db.scalar(
            select(CaggMeteoHourly).where(
                CaggMeteoHourly.monitoring_post_id == monitoring_post_id,
                CaggMeteoHourly.bucket_ms == meteo_bucket_ms,
            )
        )
        if meteo_bucket_ms is not None
        else None
    )
    meteo = (
        LatestMeteoHourlyOut(
            bucket_ms=meteo_bucket_ms,
            atm_press=to_float(meteo_row.atm_press_avg),
            air_temp=to_float(meteo_row.air_temp_avg),
            air_hum=to_float(meteo_row.air_hum_avg),
            hor_win_dir=to_float(meteo_row.hor_win_dir_avg),
            hor_win_spd=to_float(meteo_row.hor_win_spd_avg),
        )
        if meteo_row
        else None
    )

    ivtm_row = (
        db.scalar(
            select(CaggIvtmHourly).where(
                CaggIvtmHourly.monitoring_post_id == monitoring_post_id,
                CaggIvtmHourly.bucket_ms == ivtm_bucket_ms,
            )
        )
        if ivtm_bucket_ms is not None
        else None
    )
    ivtm = (
        LatestIvtmHourlyOut(
            bucket_ms=ivtm_bucket_ms,
            sensor_ivtm_hum=to_float(ivtm_row.sensor_ivtm_hum_avg),
            sensor_ivtm_temp=to_float(ivtm_row.sensor_ivtm_temp_avg),
        )
        if ivtm_row
        else None
    )

    return StationLatestHourlyResponse(
        monitoring_post_id=monitoring_post_id,
        bucket_ms=latest_bucket_ms,
        gas=gas,
        dust=dust,
        meteo=meteo,
        ivtm=ivtm,
    )
