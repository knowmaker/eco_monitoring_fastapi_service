from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.query_params import parse_datetime_range_query, parse_month_query
from app.core.dates import current_local_date, to_epoch_ms
from app.db.session import get_db
from app.models.cagg_meteo_daily import CaggMeteoDaily
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.models.meteo_state import MeteoState
from app.schemas.meteo_state import (
    MeteoStateDayPoint,
    MeteoStateHourlyResponse,
    MeteoStateHourPoint,
    MeteoStateMetricSeriesOut,
    MeteoStateMonthlyResponse,
    MeteoStateRawMetricSeriesOut,
    MeteoStateRawPoint,
    MeteoStateRawResponse,
)
from app.services.aggregate_readings import MetricSpec, build_metric_series, hourly_metric_values, monthly_metric_values
from app.services.raw_readings import build_raw_metric_series, raw_metric_rows


router = APIRouter(prefix="/meteo-state", tags=["meteo-state"])

HOURLY_METRICS = [
    MetricSpec("atm_press", CaggMeteoHourly.atm_press_avg),
    MetricSpec("air_temp", CaggMeteoHourly.air_temp_avg),
    MetricSpec("air_hum", CaggMeteoHourly.air_hum_avg),
    MetricSpec("hor_win_dir", CaggMeteoHourly.hor_win_dir_avg),
    MetricSpec("hor_win_spd", CaggMeteoHourly.hor_win_spd_avg),
]

DAILY_METRICS = [
    MetricSpec("atm_press", CaggMeteoDaily.atm_press_avg),
    MetricSpec("air_temp", CaggMeteoDaily.air_temp_avg),
    MetricSpec("air_hum", CaggMeteoDaily.air_hum_avg),
    MetricSpec("hor_win_dir", CaggMeteoDaily.hor_win_dir_avg),
    MetricSpec("hor_win_spd", CaggMeteoDaily.hor_win_spd_avg),
]

RAW_METRICS = [
    MetricSpec("atm_press", MeteoState.atm_press),
    MetricSpec("air_temp", MeteoState.air_temp),
    MetricSpec("air_hum", MeteoState.air_hum),
    MetricSpec("hor_win_dir", MeteoState.hor_win_dir),
    MetricSpec("hor_win_spd", MeteoState.hor_win_spd),
]


@router.get("/hourly", response_model=MeteoStateHourlyResponse)
def get_hourly_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> MeteoStateHourlyResponse:
    day = target_date or current_local_date()
    values = hourly_metric_values(db, CaggMeteoHourly, monitoring_post_id, day, HOURLY_METRICS)
    series = build_metric_series(
        values,
        HOURLY_METRICS,
        MeteoStateHourPoint,
        MeteoStateMetricSeriesOut,
        "hour",
        range(24),
    )
    return MeteoStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=MeteoStateMonthlyResponse)
def get_monthly_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> MeteoStateMonthlyResponse:
    period = parse_month_query(target_month)
    values = monthly_metric_values(db, CaggMeteoDaily, monitoring_post_id, period.year, period.month, DAILY_METRICS)
    series = build_metric_series(
        values,
        DAILY_METRICS,
        MeteoStateDayPoint,
        MeteoStateMetricSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    return MeteoStateMonthlyResponse(month=period.key, series=series)


@router.get("/raw", response_model=MeteoStateRawResponse)
def get_raw_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    start_value: str = Query(..., alias="from"),
    end_value: str = Query(..., alias="to"),
    _current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeteoStateRawResponse:
    start, end = parse_datetime_range_query(start_value, end_value)
    rows = raw_metric_rows(db, MeteoState, monitoring_post_id, to_epoch_ms(start), to_epoch_ms(end), RAW_METRICS)
    series = build_raw_metric_series(rows, RAW_METRICS, MeteoStateRawPoint, MeteoStateRawMetricSeriesOut)
    return MeteoStateRawResponse(start=start.isoformat(), end=end.isoformat(), series=series)
