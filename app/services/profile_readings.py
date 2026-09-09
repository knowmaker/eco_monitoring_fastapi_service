from datetime import date
from typing import Any

from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.core.dates import APP_TIMEZONE
from app.core.values import to_float
from app.models.cagg_profile_inversion_daily import CaggProfileInversionDaily
from app.models.cagg_profile_inversion_hourly import CaggProfileInversionHourly
from app.models.cagg_profile_levels_daily import CaggProfileLevelsDaily
from app.models.cagg_profile_levels_hourly import CaggProfileLevelsHourly
from app.schemas.profile_state import (
    ProfileDayOut,
    ProfileHourOut,
    ProfileInversionOut,
    ProfileLevelPointOut,
)


def get_hourly_profiles(db: Session, monitoring_post_id: int, day: date) -> list[ProfileHourOut]:
    level_rows = _fetch_hourly_levels(db, monitoring_post_id, day)
    inversion_rows = _fetch_hourly_inversions(db, monitoring_post_id, day)
    levels_by_hour = _levels_by_period(level_rows, "hour")
    inversions_by_hour = _inversions_by_period(inversion_rows, "hour")

    return [
        ProfileHourOut(
            hour=hour,
            levels=levels_by_hour.get(hour, []),
            inversion=inversions_by_hour.get(hour),
        )
        for hour in range(24)
    ]


def get_monthly_profiles(
    db: Session,
    monitoring_post_id: int,
    year: int,
    month: int,
    days_count: int,
) -> list[ProfileDayOut]:
    level_rows = _fetch_monthly_levels(db, monitoring_post_id, year, month)
    inversion_rows = _fetch_monthly_inversions(db, monitoring_post_id, year, month)
    levels_by_day = _levels_by_period(level_rows, "day")
    inversions_by_day = _inversions_by_period(inversion_rows, "day")

    return [
        ProfileDayOut(
            day=day,
            levels=levels_by_day.get(day, []),
            inversion=inversions_by_day.get(day),
        )
        for day in range(1, days_count + 1)
    ]


def _to_inversion(power: object, lower: object, upper: object, delta_t: object) -> ProfileInversionOut | None:
    power_value = to_float(power)
    if power_value is None or power_value <= 0:
        return None
    return ProfileInversionOut(
        power=power_value,
        lower=to_float(lower),
        upper=to_float(upper),
        deltaT=to_float(delta_t),
    )


def _fetch_hourly_levels(db: Session, monitoring_post_id: int, day: date) -> list[Any]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileLevelsHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    return db.execute(
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


def _fetch_hourly_inversions(db: Session, monitoring_post_id: int, day: date) -> list[Any]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileInversionHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    return db.execute(
        select(
            hour_expr.label("hour"),
            CaggProfileInversionHourly.inversion_power_avg.label("power"),
            CaggProfileInversionHourly.inversion_lower_avg.label("lower"),
            CaggProfileInversionHourly.inversion_upper_avg.label("upper"),
            CaggProfileInversionHourly.inversion_delta_t_avg.label("delta_t"),
        )
        .where(
            CaggProfileInversionHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
    ).all()


def _fetch_monthly_levels(db: Session, monitoring_post_id: int, year: int, month: int) -> list[Any]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileLevelsDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    return db.execute(
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


def _fetch_monthly_inversions(db: Session, monitoring_post_id: int, year: int, month: int) -> list[Any]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggProfileInversionDaily.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    return db.execute(
        select(
            day_expr.label("day"),
            CaggProfileInversionDaily.inversion_power_avg.label("power"),
            CaggProfileInversionDaily.inversion_lower_avg.label("lower"),
            CaggProfileInversionDaily.inversion_upper_avg.label("upper"),
            CaggProfileInversionDaily.inversion_delta_t_avg.label("delta_t"),
        )
        .where(
            CaggProfileInversionDaily.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
    ).all()


def _levels_by_period(rows: list[Any], period_field: str) -> dict[int, list[ProfileLevelPointOut]]:
    levels_by_period: dict[int, list[ProfileLevelPointOut]] = {}
    for row in rows:
        levels_by_period.setdefault(int(getattr(row, period_field)), []).append(
            ProfileLevelPointOut(
                height=float(row.height),
                temperature=to_float(row.temperature),
            )
        )
    return levels_by_period


def _inversions_by_period(rows: list[Any], period_field: str) -> dict[int, ProfileInversionOut | None]:
    return {
        int(getattr(row, period_field)): _to_inversion(row.power, row.lower, row.upper, row.delta_t)
        for row in rows
    }
