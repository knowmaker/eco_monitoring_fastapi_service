from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.query_params import parse_month_query
from app.core.dates import current_local_date
from app.db.session import get_db
from app.models.cagg_dust_daily import CaggDustDaily
from app.models.cagg_dust_hourly import CaggDustHourly
from app.schemas.dust_state import (
    DustStateDayPoint,
    DustStateHourlyResponse,
    DustStateHourPoint,
    DustStateMetricSeriesOut,
    DustStateMonthlyResponse,
)
from app.services.aggregate_readings import MetricSpec, build_metric_series, hourly_metric_values, monthly_metric_values


router = APIRouter(prefix="/dust-state", tags=["dust-state"])

HOURLY_METRICS = [
    MetricSpec("pm1_concentration", CaggDustHourly.pm1_avg),
    MetricSpec("pm2_concentration", CaggDustHourly.pm2_avg),
    MetricSpec("pm10_concentration", CaggDustHourly.pm10_avg),
    MetricSpec("tsp_concentration", CaggDustHourly.tsp_avg),
]

DAILY_METRICS = [
    MetricSpec("pm1_concentration", CaggDustDaily.pm1_avg),
    MetricSpec("pm2_concentration", CaggDustDaily.pm2_avg),
    MetricSpec("pm10_concentration", CaggDustDaily.pm10_avg),
    MetricSpec("tsp_concentration", CaggDustDaily.tsp_avg),
]


@router.get("/hourly", response_model=DustStateHourlyResponse)
def get_hourly_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> DustStateHourlyResponse:
    day = target_date or current_local_date()
    values = hourly_metric_values(db, CaggDustHourly, monitoring_post_id, day, HOURLY_METRICS)
    series = build_metric_series(
        values,
        HOURLY_METRICS,
        DustStateHourPoint,
        DustStateMetricSeriesOut,
        "hour",
        range(24),
    )
    return DustStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=DustStateMonthlyResponse)
def get_monthly_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> DustStateMonthlyResponse:
    period = parse_month_query(target_month)
    values = monthly_metric_values(db, CaggDustDaily, monitoring_post_id, period.year, period.month, DAILY_METRICS)
    series = build_metric_series(
        values,
        DAILY_METRICS,
        DustStateDayPoint,
        DustStateMetricSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    return DustStateMonthlyResponse(month=period.key, series=series)
