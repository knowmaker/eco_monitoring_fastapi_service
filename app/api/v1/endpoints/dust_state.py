from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.query_params import parse_datetime_range_query, parse_month_query
from app.core.dates import current_local_date, to_epoch_ms
from app.db.session import get_db
from app.models.cagg_dust_daily import CaggDustDaily
from app.models.cagg_dust_hourly import CaggDustHourly
from app.models.dust_state import DustState
from app.schemas.dust_state import (
    DustStateDayPoint,
    DustStateHourlyResponse,
    DustStateHourPoint,
    DustStateMetricSeriesOut,
    DustStateMonthlyResponse,
    DustStateRawMetricSeriesOut,
    DustStateRawPoint,
    DustStateRawResponse,
)
from app.services.aggregate_readings import MetricSpec, build_metric_series, hourly_metric_values, monthly_metric_values
from app.services.raw_readings import build_raw_metric_series, raw_metric_rows


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

RAW_METRICS = [
    MetricSpec("pm1_concentration", DustState.pm1_concentration),
    MetricSpec("pm2_concentration", DustState.pm2_concentration),
    MetricSpec("pm10_concentration", DustState.pm10_concentration),
    MetricSpec("tsp_concentration", DustState.tsp_concentration),
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


@router.get("/raw", response_model=DustStateRawResponse)
def get_raw_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    start_value: str = Query(..., alias="from"),
    end_value: str = Query(..., alias="to"),
    _current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DustStateRawResponse:
    start, end = parse_datetime_range_query(start_value, end_value)
    rows = raw_metric_rows(db, DustState, monitoring_post_id, to_epoch_ms(start), to_epoch_ms(end), RAW_METRICS)
    series = build_raw_metric_series(rows, RAW_METRICS, DustStateRawPoint, DustStateRawMetricSeriesOut)
    return DustStateRawResponse(start=start.isoformat(), end=end.isoformat(), series=series)
