from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.query_params import parse_month_query
from app.core.dates import current_local_date
from app.db.session import get_db
from app.models.cagg_ivtm_daily import CaggIvtmDaily
from app.models.cagg_ivtm_hourly import CaggIvtmHourly
from app.schemas.ivtm_state import (
    IvtmStateDayPoint,
    IvtmStateHourlyResponse,
    IvtmStateHourPoint,
    IvtmStateMetricSeriesOut,
    IvtmStateMonthlyResponse,
)
from app.services.aggregate_readings import MetricSpec, build_metric_series, hourly_metric_values, monthly_metric_values


router = APIRouter(prefix="/ivtm-state", tags=["ivtm-state"])

HOURLY_METRICS = [
    MetricSpec("sensor_ivtm_hum", CaggIvtmHourly.sensor_ivtm_hum_avg),
    MetricSpec("sensor_ivtm_temp", CaggIvtmHourly.sensor_ivtm_temp_avg),
]

DAILY_METRICS = [
    MetricSpec("sensor_ivtm_hum", CaggIvtmDaily.sensor_ivtm_hum_avg),
    MetricSpec("sensor_ivtm_temp", CaggIvtmDaily.sensor_ivtm_temp_avg),
]


@router.get("/hourly", response_model=IvtmStateHourlyResponse)
def get_hourly_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> IvtmStateHourlyResponse:
    day = target_date or current_local_date()
    values = hourly_metric_values(db, CaggIvtmHourly, monitoring_post_id, day, HOURLY_METRICS)
    series = build_metric_series(
        values,
        HOURLY_METRICS,
        IvtmStateHourPoint,
        IvtmStateMetricSeriesOut,
        "hour",
        range(24),
    )
    return IvtmStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=IvtmStateMonthlyResponse)
def get_monthly_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> IvtmStateMonthlyResponse:
    period = parse_month_query(target_month)
    values = monthly_metric_values(db, CaggIvtmDaily, monitoring_post_id, period.year, period.month, DAILY_METRICS)
    series = build_metric_series(
        values,
        DAILY_METRICS,
        IvtmStateDayPoint,
        IvtmStateMetricSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    return IvtmStateMonthlyResponse(month=period.key, series=series)
