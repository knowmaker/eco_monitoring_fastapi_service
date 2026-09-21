from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.query_params import parse_datetime_range_query, parse_month_query
from app.core.dates import current_local_date, to_epoch_ms
from app.db.session import get_db
from app.models.cagg_ivtm_daily import CaggIvtmDaily
from app.models.cagg_ivtm_hourly import CaggIvtmHourly
from app.models.ivtm_state import IvtmState
from app.schemas.ivtm_state import (
    IvtmStateDayPoint,
    IvtmStateHourlyResponse,
    IvtmStateHourPoint,
    IvtmStateMetricSeriesOut,
    IvtmStateMonthlyResponse,
    IvtmStateRawMetricSeriesOut,
    IvtmStateRawPoint,
    IvtmStateRawResponse,
)
from app.services.aggregate_readings import MetricSpec, build_metric_series, hourly_metric_values, monthly_metric_values
from app.services.raw_readings import build_raw_metric_series, raw_metric_rows


router = APIRouter(prefix="/ivtm-state", tags=["ivtm-state"])

HOURLY_METRICS = [
    MetricSpec("sensor_ivtm_hum", CaggIvtmHourly.sensor_ivtm_hum_avg),
    MetricSpec("sensor_ivtm_temp", CaggIvtmHourly.sensor_ivtm_temp_avg),
]

DAILY_METRICS = [
    MetricSpec("sensor_ivtm_hum", CaggIvtmDaily.sensor_ivtm_hum_avg),
    MetricSpec("sensor_ivtm_temp", CaggIvtmDaily.sensor_ivtm_temp_avg),
]

RAW_METRICS = [
    MetricSpec("sensor_ivtm_hum", IvtmState.sensor_ivtm_hum),
    MetricSpec("sensor_ivtm_temp", IvtmState.sensor_ivtm_temp),
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


@router.get("/raw", response_model=IvtmStateRawResponse)
def get_raw_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    start_value: str = Query(..., alias="from"),
    end_value: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
) -> IvtmStateRawResponse:
    start, end = parse_datetime_range_query(start_value, end_value)
    rows = raw_metric_rows(db, IvtmState, monitoring_post_id, to_epoch_ms(start), to_epoch_ms(end), RAW_METRICS)
    series = build_raw_metric_series(rows, RAW_METRICS, IvtmStateRawPoint, IvtmStateRawMetricSeriesOut)
    return IvtmStateRawResponse(start=start.isoformat(), end=end.isoformat(), series=series)
