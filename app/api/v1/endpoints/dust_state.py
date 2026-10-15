from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.query_params import parse_datetime_range_query, parse_month_query
from app.core.dates import current_local_date, to_epoch_ms
from app.core.mosecom import MOSECOM_DUST_CODES, MOSECOM_DUST_CODE_TO_METRIC
from app.db.session import get_db
from app.models.cagg_dust_daily import CaggDustDaily
from app.models.cagg_dust_hourly import CaggDustHourly
from app.models.dust_state import DustState
from app.models.monitoring_posts import MonitoringPost
from app.models.mosecom_hourly_reading import MosecomHourlyReading
from app.models.pollutant_limit import PollutantLimit
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
from app.services.aggregate_readings import (
    MetricSpec,
    build_metric_series,
    hourly_metric_values,
    hourly_substance_values,
    monthly_hourly_substance_values,
    monthly_metric_values,
)
from app.services.raw_readings import build_raw_metric_series, raw_metric_rows


router = APIRouter(prefix="/dust-state", tags=["dust-state"])

DUST_POLLUTANT_BY_METRIC = {
    "pm1_concentration": "PM1",
    "pm2_concentration": "PM2.5",
    "pm10_concentration": "PM10",
    "tsp_concentration": "TSP",
}

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
    if _is_mosecom_post(db, monitoring_post_id):
        substance_values = hourly_substance_values(
            db, MosecomHourlyReading, monitoring_post_id, day, MOSECOM_DUST_CODES
        )
        series = _build_mosecom_series(substance_values, DustStateHourPoint, "hour", range(24))
        _set_pdk_values(db, series)
        return DustStateHourlyResponse(date=day.isoformat(), series=series)

    values = hourly_metric_values(db, CaggDustHourly, monitoring_post_id, day, HOURLY_METRICS)
    series = build_metric_series(
        values,
        HOURLY_METRICS,
        DustStateHourPoint,
        DustStateMetricSeriesOut,
        "hour",
        range(24),
    )
    series = _filter_empty_series(series)
    _set_pdk_values(db, series)
    return DustStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=DustStateMonthlyResponse)
def get_monthly_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> DustStateMonthlyResponse:
    period = parse_month_query(target_month)
    if _is_mosecom_post(db, monitoring_post_id):
        substance_values = monthly_hourly_substance_values(
            db,
            MosecomHourlyReading,
            monitoring_post_id,
            period.year,
            period.month,
            MOSECOM_DUST_CODES,
        )
        series = _build_mosecom_series(
            substance_values,
            DustStateDayPoint,
            "day",
            range(1, period.days_count + 1),
        )
        _set_pdk_values(db, series)
        return DustStateMonthlyResponse(month=period.key, series=series)

    values = monthly_metric_values(db, CaggDustDaily, monitoring_post_id, period.year, period.month, DAILY_METRICS)
    series = build_metric_series(
        values,
        DAILY_METRICS,
        DustStateDayPoint,
        DustStateMetricSeriesOut,
        "day",
        range(1, period.days_count + 1),
    )
    series = _filter_empty_series(series)
    _set_pdk_values(db, series)
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
    series = _filter_empty_series(series)
    _set_pdk_values(db, series)
    return DustStateRawResponse(start=start.isoformat(), end=end.isoformat(), series=series)


def _is_mosecom_post(db: Session, monitoring_post_id: int) -> bool:
    return db.scalar(
        select(MonitoringPost.source).where(MonitoringPost.id == monitoring_post_id)
    ) == "mosecom"


def _build_mosecom_series(
    values_by_substance: dict[str, dict[int, float | None]],
    point_model: type,
    period_field: str,
    periods: range,
) -> list[DustStateMetricSeriesOut]:
    return [
        DustStateMetricSeriesOut(
            key=metric_key,
            points=[
                point_model(**{period_field: period, "value": values_by_substance.get(code, {}).get(period)})
                for period in periods
            ],
        )
        for code, metric_key in MOSECOM_DUST_CODE_TO_METRIC.items()
        if code in values_by_substance
    ]


def _filter_empty_series(
    series: list[DustStateMetricSeriesOut] | list[DustStateRawMetricSeriesOut],
) -> list[DustStateMetricSeriesOut] | list[DustStateRawMetricSeriesOut]:
    return [item for item in series if any(point.value is not None for point in item.points)]


def _set_pdk_values(
    db: Session,
    series: list[DustStateMetricSeriesOut] | list[DustStateRawMetricSeriesOut],
) -> None:
    if not series:
        return

    pollutant_codes = [DUST_POLLUTANT_BY_METRIC[item.key] for item in series]
    pdk_by_code = dict(
        db.execute(
            select(PollutantLimit.pollutant_code, PollutantLimit.pdk_max_once).where(
                PollutantLimit.pollutant_code.in_(pollutant_codes)
            )
        ).all()
    )
    for item in series:
        item.pdk = pdk_by_code.get(DUST_POLLUTANT_BY_METRIC[item.key])
