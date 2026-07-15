import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

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


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/ivtm_state", tags=["ivtm_state"])


def parse_month(value: str | None) -> tuple[int, int, str, int]:
    if value is None:
        now = datetime.now(ZoneInfo(APP_TIMEZONE))
        year, month = now.year, now.month
    else:
        try:
            year_text, month_text = value.split("-", 1)
            year, month = int(year_text), int(month_text)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="month must use YYYY-MM format") from exc

    days_in_month = calendar.monthrange(year, month)[1]
    return year, month, f"{year:04d}-{month:02d}", days_in_month


@router.get("/hourly", response_model=IvtmStateHourlyResponse)
def get_hourly_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> IvtmStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggIvtmHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            hour_expr.label("hour"),
            CaggIvtmHourly.sensor_ivtm_hum_avg.label("sensor_ivtm_hum"),
            CaggIvtmHourly.sensor_ivtm_temp_avg.label("sensor_ivtm_temp"),
        )
        .where(
            CaggIvtmHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(hour_expr.asc())
    ).all()

    by_hour: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_hour[int(row.hour)] = {
            "sensor_ivtm_hum": float(row.sensor_ivtm_hum) if row.sensor_ivtm_hum is not None else None,
            "sensor_ivtm_temp": float(row.sensor_ivtm_temp) if row.sensor_ivtm_temp is not None else None,
        }

    metric_keys = [
        "sensor_ivtm_hum",
        "sensor_ivtm_temp",
    ]
    series = []
    for key in metric_keys:
        points = [IvtmStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(IvtmStateMetricSeriesOut(key=key, points=points))

    return IvtmStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=IvtmStateMonthlyResponse)
def get_monthly_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> IvtmStateMonthlyResponse:
    year, month, month_key, days_in_month = parse_month(target_month)

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggIvtmDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    rows = db.execute(
        select(
            day_expr.label("day"),
            CaggIvtmDaily.sensor_ivtm_hum_avg.label("sensor_ivtm_hum"),
            CaggIvtmDaily.sensor_ivtm_temp_avg.label("sensor_ivtm_temp"),
        )
        .where(
            CaggIvtmDaily.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(day_expr.asc())
    ).all()

    by_day: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_day[int(row.day)] = {
            "sensor_ivtm_hum": float(row.sensor_ivtm_hum) if row.sensor_ivtm_hum is not None else None,
            "sensor_ivtm_temp": float(row.sensor_ivtm_temp) if row.sensor_ivtm_temp is not None else None,
        }

    metric_keys = [
        "sensor_ivtm_hum",
        "sensor_ivtm_temp",
    ]
    series = []
    for key in metric_keys:
        points = [IvtmStateDayPoint(day=d, value=by_day.get(d, {}).get(key)) for d in range(1, days_in_month + 1)]
        series.append(IvtmStateMetricSeriesOut(key=key, points=points))

    return IvtmStateMonthlyResponse(month=month_key, series=series)
