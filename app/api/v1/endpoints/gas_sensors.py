from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.query_params import parse_month_query
from app.core.dates import current_local_date
from app.db.session import get_db
from app.models.cagg_gas_daily import CaggGasDaily
from app.models.cagg_gas_hourly import CaggGasHourly
from app.schemas.gas_sensors import (
    GasSensorsDayPoint,
    GasSensorsHourPoint,
    GasSensorsHourlyResponse,
    GasSensorsMonthlyResponse,
    GasSensorsSubstanceSeriesOut,
)
from app.services.aggregate_readings import build_substance_series, hourly_substance_values, monthly_substance_values


router = APIRouter(prefix="/gas-sensors", tags=["gas-sensors"])


@router.get("/hourly", response_model=GasSensorsHourlyResponse)
def get_hourly_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> GasSensorsHourlyResponse:
    day = target_date or current_local_date()
    values = hourly_substance_values(db, CaggGasHourly, monitoring_post_id, day)
    substances = build_substance_series(values, GasSensorsHourPoint, GasSensorsSubstanceSeriesOut, "hour", range(24))
    return GasSensorsHourlyResponse(date=day.isoformat(), substances=substances)


@router.get("/monthly", response_model=GasSensorsMonthlyResponse)
def get_monthly_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> GasSensorsMonthlyResponse:
    period = parse_month_query(target_month)
    values = monthly_substance_values(db, CaggGasDaily, monitoring_post_id, period.year, period.month)
    substances = build_substance_series(
        values,
        GasSensorsDayPoint,
        GasSensorsSubstanceSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    return GasSensorsMonthlyResponse(month=period.key, substances=substances)
