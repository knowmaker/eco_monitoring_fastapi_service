from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.core.dates import APP_TIMEZONE
from app.core.values import to_float


@dataclass(frozen=True)
class MetricSpec:
    key: str
    column: Any


def hourly_metric_values(
    db: Session,
    model: type,
    monitoring_post_id: int,
    day: date,
    metrics: list[MetricSpec],
) -> dict[int, dict[str, float | None]]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(model.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            hour_expr.label("period_index"),
            *(metric.column.label(metric.key) for metric in metrics),
        )
        .where(
            model.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(hour_expr.asc())
    ).all()

    return _rows_by_period(rows, metrics)


def monthly_metric_values(
    db: Session,
    model: type,
    monitoring_post_id: int,
    year: int,
    month: int,
    metrics: list[MetricSpec],
) -> dict[int, dict[str, float | None]]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(model.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    rows = db.execute(
        select(
            day_expr.label("period_index"),
            *(metric.column.label(metric.key) for metric in metrics),
        )
        .where(
            model.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(day_expr.asc())
    ).all()

    return _rows_by_period(rows, metrics)


def build_metric_series(
    values_by_period: dict[int, dict[str, float | None]],
    metrics: list[MetricSpec],
    point_model: type[BaseModel],
    series_model: type[BaseModel],
    period_field: str,
    periods: range,
) -> list[BaseModel]:
    return [
        series_model(
            key=metric.key,
            points=[
                point_model(**{period_field: period, "value": values_by_period.get(period, {}).get(metric.key)})
                for period in periods
            ],
        )
        for metric in metrics
    ]


def hourly_substance_values(
    db: Session,
    model: type,
    monitoring_post_id: int,
    day: date,
) -> dict[str, dict[int, float | None]]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(model.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            model.substance_code.label("substance_code"),
            hour_expr.label("period_index"),
            model.value_avg.label("value"),
        )
        .where(
            model.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(model.substance_code.asc(), hour_expr.asc())
    ).all()

    return _substance_rows_by_period(rows)


def monthly_substance_values(
    db: Session,
    model: type,
    monitoring_post_id: int,
    year: int,
    month: int,
) -> dict[str, dict[int, float | None]]:
    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(model.bucket_ms / 1000.0))
    day_expr = cast(func.extract("day", local_ts), Integer)
    month_expr = cast(func.extract("month", local_ts), Integer)
    year_expr = cast(func.extract("year", local_ts), Integer)

    rows = db.execute(
        select(
            model.substance_code.label("substance_code"),
            day_expr.label("period_index"),
            model.value_avg.label("value"),
        )
        .where(
            model.monitoring_post_id == monitoring_post_id,
            year_expr == year,
            month_expr == month,
        )
        .order_by(model.substance_code.asc(), day_expr.asc())
    ).all()

    return _substance_rows_by_period(rows)


def build_substance_series(
    values_by_substance: dict[str, dict[int, float | None]],
    point_model: type[BaseModel],
    series_model: type[BaseModel],
    period_field: str,
    periods: range,
) -> list[BaseModel]:
    return [
        series_model(
            substance_code=substance_code,
            points=[
                point_model(**{period_field: period, "value": values_by_period.get(period)})
                for period in periods
            ],
        )
        for substance_code, values_by_period in sorted(values_by_substance.items())
    ]


def _rows_by_period(rows: list[Any], metrics: list[MetricSpec]) -> dict[int, dict[str, float | None]]:
    values_by_period: dict[int, dict[str, float | None]] = {}
    for row in rows:
        values_by_period[int(row.period_index)] = {
            metric.key: to_float(getattr(row, metric.key))
            for metric in metrics
        }
    return values_by_period


def _substance_rows_by_period(rows: list[Any]) -> dict[str, dict[int, float | None]]:
    values_by_substance: dict[str, dict[int, float | None]] = {}
    for row in rows:
        substance_key = str(row.substance_code)
        values_by_substance.setdefault(substance_key, {})[int(row.period_index)] = to_float(row.value)
    return values_by_substance
