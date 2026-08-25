import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_profile_inversion_daily import CaggProfileInversionDaily
from app.models.cagg_profile_inversion_hourly import CaggProfileInversionHourly
from app.models.cagg_profile_levels_daily import CaggProfileLevelsDaily
from app.models.cagg_profile_levels_hourly import CaggProfileLevelsHourly
from app.schemas.profile_state import (
    ProfileDayOut,
    ProfileHourOut,
    ProfileInversionOut,
    ProfileLevelPointOut,
    ProfileStateHourlyResponse,
    ProfileStateMonthlyResponse,
)


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/profile_state", tags=["profile_state"])


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


def to_float(value: object) -> float | None:
    return float(value) if value is not None else None


def to_inversion(power: object, lower: object, upper: object) -> ProfileInversionOut | None:
    power_value = to_float(power)
    if power_value is None or power_value <= 0:
        return None
    return ProfileInversionOut(
        power=power_value,
        lower=to_float(lower),
        upper=to_float(upper),
    )


@router.get("/hourly", response_model=ProfileStateHourlyResponse)
def get_hourly_profile_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> ProfileStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileLevelsHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    level_rows = db.execute(
        select(
            hour_expr.label("hour"),
            CaggProfileLevelsHourly.height.label("height"),
            CaggProfileLevelsHourly.temperature_avg.label("temperature"),
        )
        .where(
            CaggProfileLevelsHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(hour_expr.asc(), CaggProfileLevelsHourly.height.asc())
    ).all()

    inversion_local_ts = func.timezone(
        APP_TIMEZONE,
        func.to_timestamp(CaggProfileInversionHourly.bucket_ms / 1000.0),
    )
    inversion_hour_expr = cast(func.extract("hour", inversion_local_ts), Integer)
    inversion_date_expr = cast(inversion_local_ts, Date)
    inversion_rows = db.execute(
        select(
            inversion_hour_expr.label("hour"),
            CaggProfileInversionHourly.inversion_power_avg.label("power"),
            CaggProfileInversionHourly.inversion_lower_avg.label("lower"),
            CaggProfileInversionHourly.inversion_upper_avg.label("upper"),
        )
        .where(
            CaggProfileInversionHourly.monitoring_post_id == monitoring_post_id,
            inversion_date_expr == day,
        )
    ).all()

    levels_by_hour: dict[int, list[ProfileLevelPointOut]] = {}
    for hour, height, temperature in level_rows:
        levels_by_hour.setdefault(int(hour), []).append(
            ProfileLevelPointOut(
                height=float(height),
                temperature=to_float(temperature),
            )
        )

    inversions_by_hour = {
        int(row.hour): to_inversion(row.power, row.lower, row.upper)
        for row in inversion_rows
    }

    profiles = [
        ProfileHourOut(
            hour=hour,
            levels=levels_by_hour.get(hour, []),
            inversion=inversions_by_hour.get(hour),
        )
        for hour in range(24)
    ]

    return ProfileStateHourlyResponse(date=day.isoformat(), profiles=profiles)


@router.get("/monthly", response_model=ProfileStateMonthlyResponse)
def get_monthly_profile_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> ProfileStateMonthlyResponse:
    year, month, month_key, days_in_month = parse_month(target_month)

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileLevelsDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    level_rows = db.execute(
        select(
            day_expr.label("day"),
            CaggProfileLevelsDaily.height.label("height"),
            CaggProfileLevelsDaily.temperature_avg.label("temperature"),
        )
        .where(
            CaggProfileLevelsDaily.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(day_expr.asc(), CaggProfileLevelsDaily.height.asc())
    ).all()

    inversion_local_ts = func.timezone(
        APP_TIMEZONE,
        func.to_timestamp(CaggProfileInversionDaily.bucket_ms / 1000.0),
    )
    inversion_day_expr = cast(func.extract("day", inversion_local_ts), Integer)
    inversion_month_expr = cast(func.extract("month", inversion_local_ts), Integer)
    inversion_year_expr = cast(func.extract("year", inversion_local_ts), Integer)
    inversion_rows = db.execute(
        select(
            inversion_day_expr.label("day"),
            CaggProfileInversionDaily.inversion_power_avg.label("power"),
            CaggProfileInversionDaily.inversion_lower_avg.label("lower"),
            CaggProfileInversionDaily.inversion_upper_avg.label("upper"),
        )
        .where(
            CaggProfileInversionDaily.monitoring_post_id == monitoring_post_id,
            inversion_year_expr == year,
            inversion_month_expr == month,
        )
    ).all()

    levels_by_day: dict[int, list[ProfileLevelPointOut]] = {}
    for day_number, height, temperature in level_rows:
        levels_by_day.setdefault(int(day_number), []).append(
            ProfileLevelPointOut(
                height=float(height),
                temperature=to_float(temperature),
            )
        )

    inversions_by_day = {
        int(row.day): to_inversion(row.power, row.lower, row.upper)
        for row in inversion_rows
    }

    profiles = [
        ProfileDayOut(
            day=day_number,
            levels=levels_by_day.get(day_number, []),
            inversion=inversions_by_day.get(day_number),
        )
        for day_number in range(1, days_in_month + 1)
    ]

    return ProfileStateMonthlyResponse(month=month_key, profiles=profiles)
