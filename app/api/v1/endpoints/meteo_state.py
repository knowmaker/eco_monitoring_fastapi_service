import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_meteo_daily import CaggMeteoDaily
from app.models.cagg_meteo_hourly import CaggMeteoHourly
from app.schemas.meteo_state import (
    MeteoStateDayPoint,
    MeteoStateHourlyResponse,
    MeteoStateHourPoint,
    MeteoStateMetricSeriesOut,
    MeteoStateMonthlyResponse,
)


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/meteo_state", tags=["meteo_state"])


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


@router.get("/hourly", response_model=MeteoStateHourlyResponse)
def get_hourly_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> MeteoStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggMeteoHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            hour_expr.label("hour"),
            CaggMeteoHourly.atm_press_avg.label("atm_press"),
            CaggMeteoHourly.air_temp_avg.label("air_temp"),
            CaggMeteoHourly.air_hum_avg.label("air_hum"),
            CaggMeteoHourly.hor_win_dir_avg.label("hor_win_dir"),
            CaggMeteoHourly.hor_win_spd_avg.label("hor_win_spd"),
        )
        .where(
            CaggMeteoHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(hour_expr.asc())
    ).all()

    by_hour: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_hour[int(row.hour)] = {
            "atm_press": float(row.atm_press) if row.atm_press is not None else None,
            "air_temp": float(row.air_temp) if row.air_temp is not None else None,
            "air_hum": float(row.air_hum) if row.air_hum is not None else None,
            "hor_win_dir": float(row.hor_win_dir) if row.hor_win_dir is not None else None,
            "hor_win_spd": float(row.hor_win_spd) if row.hor_win_spd is not None else None,
        }

    metric_keys = [
        "atm_press",
        "air_temp",
        "air_hum",
        "hor_win_dir",
        "hor_win_spd",
    ]
    series = []
    for key in metric_keys:
        points = [MeteoStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(MeteoStateMetricSeriesOut(key=key, points=points))

    return MeteoStateHourlyResponse(date=day.isoformat(), series=series)


@router.get("/monthly", response_model=MeteoStateMonthlyResponse)
def get_monthly_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> MeteoStateMonthlyResponse:
    year, month, month_key, days_in_month = parse_month(target_month)

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggMeteoDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    rows = db.execute(
        select(
            day_expr.label("day"),
            CaggMeteoDaily.atm_press_avg.label("atm_press"),
            CaggMeteoDaily.air_temp_avg.label("air_temp"),
            CaggMeteoDaily.air_hum_avg.label("air_hum"),
            CaggMeteoDaily.hor_win_dir_avg.label("hor_win_dir"),
            CaggMeteoDaily.hor_win_spd_avg.label("hor_win_spd"),
        )
        .where(
            CaggMeteoDaily.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(day_expr.asc())
    ).all()

    by_day: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_day[int(row.day)] = {
            "atm_press": float(row.atm_press) if row.atm_press is not None else None,
            "air_temp": float(row.air_temp) if row.air_temp is not None else None,
            "air_hum": float(row.air_hum) if row.air_hum is not None else None,
            "hor_win_dir": float(row.hor_win_dir) if row.hor_win_dir is not None else None,
            "hor_win_spd": float(row.hor_win_spd) if row.hor_win_spd is not None else None,
        }

    metric_keys = [
        "atm_press",
        "air_temp",
        "air_hum",
        "hor_win_dir",
        "hor_win_spd",
    ]
    series = []
    for key in metric_keys:
        points = [MeteoStateDayPoint(day=d, value=by_day.get(d, {}).get(key)) for d in range(1, days_in_month + 1)]
        series.append(MeteoStateMetricSeriesOut(key=key, points=points))

    return MeteoStateMonthlyResponse(month=month_key, series=series)
