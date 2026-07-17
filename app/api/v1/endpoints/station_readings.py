from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_dust_hourly import CaggDustHourly
from app.models.cagg_gas_hourly import CaggGasHourly
from app.models.cagg_ivtm_hourly import CaggIvtmHourly
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.schemas.station_readings import (
    LatestDustHourlyOut,
    LatestGasHourlyOut,
    LatestGasSubstanceOut,
    LatestIvtmHourlyOut,
    LatestMeteoHourlyOut,
    StationLatestHourlyResponse,
)


router = APIRouter(prefix="/station_readings", tags=["station_readings"])


def to_float(value: object) -> float | None:
    return float(value) if value is not None else None


@router.get("/latest_hourly", response_model=StationLatestHourlyResponse)
def get_station_latest_hourly_readings(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> StationLatestHourlyResponse:
    bucket_candidates = [
        db.scalar(select(func.max(CaggGasHourly.bucket_ms)).where(CaggGasHourly.monitoring_post_id == monitoring_post_id)),
        db.scalar(select(func.max(CaggDustHourly.bucket_ms)).where(CaggDustHourly.monitoring_post_id == monitoring_post_id)),
        db.scalar(select(func.max(CaggMeteoHourly.bucket_ms)).where(CaggMeteoHourly.monitoring_post_id == monitoring_post_id)),
        db.scalar(select(func.max(CaggIvtmHourly.bucket_ms)).where(CaggIvtmHourly.monitoring_post_id == monitoring_post_id)),
    ]
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

    gas_rows = db.execute(
        select(CaggGasHourly)
        .where(
            CaggGasHourly.monitoring_post_id == monitoring_post_id,
            CaggGasHourly.bucket_ms == latest_bucket_ms,
        )
        .order_by(CaggGasHourly.substance_code.asc())
    ).scalars().all()
    gas = (
        LatestGasHourlyOut(
            substances=[
                LatestGasSubstanceOut(substance_code=row.substance_code, value=to_float(row.value_avg))
                for row in gas_rows
            ]
        )
        if gas_rows
        else None
    )

    dust_row = db.scalar(
        select(CaggDustHourly).where(
            CaggDustHourly.monitoring_post_id == monitoring_post_id,
            CaggDustHourly.bucket_ms == latest_bucket_ms,
        )
    )
    dust = (
        LatestDustHourlyOut(
            humidity=to_float(dust_row.humidity_avg),
            temp=to_float(dust_row.temp_avg),
            pm1=to_float(dust_row.pm1_avg),
            pm2=to_float(dust_row.pm2_avg),
            pm10=to_float(dust_row.pm10_avg),
            tsp=to_float(dust_row.tsp_avg),
        )
        if dust_row
        else None
    )

    meteo_row = db.scalar(
        select(CaggMeteoHourly).where(
            CaggMeteoHourly.monitoring_post_id == monitoring_post_id,
            CaggMeteoHourly.bucket_ms == latest_bucket_ms,
        )
    )
    meteo = (
        LatestMeteoHourlyOut(
            atm_press=to_float(meteo_row.atm_press_avg),
            air_temp=to_float(meteo_row.air_temp_avg),
            air_hum=to_float(meteo_row.air_hum_avg),
            hor_win_dir=to_float(meteo_row.hor_win_dir_avg),
            hor_win_spd=to_float(meteo_row.hor_win_spd_avg),
        )
        if meteo_row
        else None
    )

    ivtm_row = db.scalar(
        select(CaggIvtmHourly).where(
            CaggIvtmHourly.monitoring_post_id == monitoring_post_id,
            CaggIvtmHourly.bucket_ms == latest_bucket_ms,
        )
    )
    ivtm = (
        LatestIvtmHourlyOut(
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
