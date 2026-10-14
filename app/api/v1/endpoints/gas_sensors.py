from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.query_params import parse_datetime_range_query, parse_month_query
from app.core.dates import current_local_date, to_epoch_ms
from app.core.mosecom import MOSECOM_GAS_CODES
from app.db.session import get_db
from app.models.cagg_gas_daily import CaggGasDaily
from app.models.cagg_gas_hourly import CaggGasHourly
from app.models.gas_sensors import GasSensors
from app.models.monitoring_posts import MonitoringPost
from app.models.mosecom_hourly_reading import MosecomHourlyReading
from app.models.pollutant_limit import PollutantLimit
from app.schemas.gas_sensors import (
    GasSensorsDayPoint,
    GasSensorsHourPoint,
    GasSensorsHourlyResponse,
    GasSensorsMonthlyResponse,
    GasSensorsRawPoint,
    GasSensorsRawResponse,
    GasSensorsRawSubstanceSeriesOut,
    GasSensorsSubstanceSeriesOut,
)
from app.services.aggregate_readings import (
    build_substance_series,
    hourly_substance_values,
    monthly_hourly_substance_values,
    monthly_substance_values,
)
from app.services.raw_readings import build_raw_substance_series, raw_substance_rows


router = APIRouter(prefix="/gas-sensors", tags=["gas-sensors"])


@router.get("/hourly", response_model=GasSensorsHourlyResponse)
def get_hourly_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> GasSensorsHourlyResponse:
    day = target_date or current_local_date()
    model = _hourly_model(db, monitoring_post_id)
    substance_codes = MOSECOM_GAS_CODES if model is MosecomHourlyReading else None
    values = hourly_substance_values(db, model, monitoring_post_id, day, substance_codes)
    substances = build_substance_series(values, GasSensorsHourPoint, GasSensorsSubstanceSeriesOut, "hour", range(24))
    _set_pdk_values(db, substances)
    return GasSensorsHourlyResponse(date=day.isoformat(), substances=substances)


@router.get("/monthly", response_model=GasSensorsMonthlyResponse)
def get_monthly_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> GasSensorsMonthlyResponse:
    period = parse_month_query(target_month)
    if _is_mosecom_post(db, monitoring_post_id):
        values = monthly_hourly_substance_values(
            db,
            MosecomHourlyReading,
            monitoring_post_id,
            period.year,
            period.month,
            MOSECOM_GAS_CODES,
        )
    else:
        values = monthly_substance_values(db, CaggGasDaily, monitoring_post_id, period.year, period.month)
    substances = build_substance_series(
        values,
        GasSensorsDayPoint,
        GasSensorsSubstanceSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    _set_pdk_values(db, substances)
    return GasSensorsMonthlyResponse(month=period.key, substances=substances)


@router.get("/raw", response_model=GasSensorsRawResponse)
def get_raw_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    start_value: str = Query(..., alias="from"),
    end_value: str = Query(..., alias="to"),
    _current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GasSensorsRawResponse:
    start, end = parse_datetime_range_query(start_value, end_value)
    rows = raw_substance_rows(db, GasSensors, monitoring_post_id, to_epoch_ms(start), to_epoch_ms(end))
    substances = build_raw_substance_series(rows, GasSensorsRawPoint, GasSensorsRawSubstanceSeriesOut)
    _set_pdk_values(db, substances)
    return GasSensorsRawResponse(start=start.isoformat(), end=end.isoformat(), substances=substances)


def _hourly_model(db: Session, monitoring_post_id: int) -> type:
    return MosecomHourlyReading if _is_mosecom_post(db, monitoring_post_id) else CaggGasHourly


def _is_mosecom_post(db: Session, monitoring_post_id: int) -> bool:
    return db.scalar(
        select(MonitoringPost.source).where(MonitoringPost.id == monitoring_post_id)
    ) == "mosecom"


def _set_pdk_values(
    db: Session,
    substances: list[GasSensorsSubstanceSeriesOut] | list[GasSensorsRawSubstanceSeriesOut],
) -> None:
    if not substances:
        return

    pdk_by_code = dict(
        db.execute(
            select(PollutantLimit.pollutant_code, PollutantLimit.pdk_max_once).where(
                PollutantLimit.pollutant_code.in_([item.substance_code for item in substances])
            )
        ).all()
    )
    for item in substances:
        item.pdk = pdk_by_code.get(item.substance_code)
