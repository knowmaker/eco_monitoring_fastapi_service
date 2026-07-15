import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

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


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/dust_state", tags=["dust_state"])


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


@router.get("/hourly", response_model=DustStateHourlyResponse)
def get_hourly_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> DustStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggDustHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            hour_expr.label("hour"),
            CaggDustHourly.pm1_avg.label("pm1_concentration"),
            CaggDustHourly.pm2_avg.label("pm2_concentration"),
            CaggDustHourly.pm10_avg.label("pm10_concentration"),
            CaggDustHourly.tsp_avg.label("tsp_concentration"),
        )
        .where(
            CaggDustHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(hour_expr.asc())
    ).all()

    by_hour: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_hour[int(row.hour)] = {
            "pm1_concentration": float(row.pm1_concentration) if row.pm1_concentration is not None else None,
            "pm2_concentration": float(row.pm2_concentration) if row.pm2_concentration is not None else None,
            "pm10_concentration": float(row.pm10_concentration) if row.pm10_concentration is not None else None,
            "tsp_concentration": float(row.tsp_concentration) if row.tsp_concentration is not None else None,
        }

    metric_keys = [
        "pm1_concentration",
        "pm2_concentration",
        "pm10_concentration",
        "tsp_concentration",
    ]
    series = []
    for key in metric_keys:
        points = [DustStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(DustStateMetricSeriesOut(key=key, points=points))

    return DustStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=DustStateMonthlyResponse)
def get_monthly_dust_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> DustStateMonthlyResponse:
    year, month, month_key, days_in_month = parse_month(target_month)

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggDustDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    rows = db.execute(
        select(
            day_expr.label("day"),
            CaggDustDaily.pm1_avg.label("pm1_concentration"),
            CaggDustDaily.pm2_avg.label("pm2_concentration"),
            CaggDustDaily.pm10_avg.label("pm10_concentration"),
            CaggDustDaily.tsp_avg.label("tsp_concentration"),
        )
        .where(
            CaggDustDaily.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(day_expr.asc())
    ).all()

    by_day: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_day[int(row.day)] = {
            "pm1_concentration": float(row.pm1_concentration) if row.pm1_concentration is not None else None,
            "pm2_concentration": float(row.pm2_concentration) if row.pm2_concentration is not None else None,
            "pm10_concentration": float(row.pm10_concentration) if row.pm10_concentration is not None else None,
            "tsp_concentration": float(row.tsp_concentration) if row.tsp_concentration is not None else None,
        }

    metric_keys = [
        "pm1_concentration",
        "pm2_concentration",
        "pm10_concentration",
        "tsp_concentration",
    ]
    series = []
    for key in metric_keys:
        points = [DustStateDayPoint(day=d, value=by_day.get(d, {}).get(key)) for d in range(1, days_in_month + 1)]
        series.append(DustStateMetricSeriesOut(key=key, points=points))

    return DustStateMonthlyResponse(month=month_key, series=series)
