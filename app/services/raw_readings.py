from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.dates import APP_ZONEINFO
from app.core.values import to_float
from app.models.device_state import DeviceState
from app.models.plc_state import PlcState
from app.services.aggregate_readings import MetricSpec


def raw_metric_rows(
    db: Session,
    model: type,
    monitoring_post_id: int,
    start_ms: int,
    end_ms: int,
    metrics: list[MetricSpec],
) -> list[Any]:
    rows = db.execute(
        select(
            model.device_timestamp_ms.label("timestamp_ms"),
            *(metric.column.label(metric.key) for metric in metrics),
        )
        .join(DeviceState, DeviceState.id == model.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            model.device_timestamp_ms >= start_ms,
            model.device_timestamp_ms < end_ms,
            or_(*(metric.column.is_not(None) for metric in metrics)),
        )
        .order_by(model.device_timestamp_ms.asc())
    ).all()
    return rows


def build_raw_metric_series(
    rows: list[Any],
    metrics: list[MetricSpec],
    point_model: type[BaseModel],
    series_model: type[BaseModel],
) -> list[BaseModel]:
    return [
        series_model(
            key=metric.key,
            points=[
                point_model(timestamp=_timestamp_label(row.timestamp_ms), value=to_float(getattr(row, metric.key)))
                for row in rows
                if getattr(row, metric.key) is not None
            ],
        )
        for metric in metrics
    ]


def raw_substance_rows(
    db: Session,
    model: type,
    monitoring_post_id: int,
    start_ms: int,
    end_ms: int,
) -> list[Any]:
    rows = db.execute(
        select(
            model.substance_code.label("substance_code"),
            model.device_timestamp_ms.label("timestamp_ms"),
            model.value.label("value"),
        )
        .join(DeviceState, DeviceState.id == model.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            model.device_timestamp_ms >= start_ms,
            model.device_timestamp_ms < end_ms,
            model.substance_code.is_not(None),
            model.value.is_not(None),
        )
        .order_by(model.substance_code.asc(), model.device_timestamp_ms.asc(), model.sensor_id.asc())
    ).all()
    return rows


def build_raw_substance_series(
    rows: list[Any],
    point_model: type[BaseModel],
    series_model: type[BaseModel],
) -> list[BaseModel]:
    values_by_substance: dict[str, list[Any]] = {}
    for row in rows:
        values_by_substance.setdefault(str(row.substance_code), []).append(row)

    return [
        series_model(
            substance_code=substance_code,
            points=[
                point_model(timestamp=_timestamp_label(row.timestamp_ms), value=to_float(row.value))
                for row in substance_rows
            ],
        )
        for substance_code, substance_rows in sorted(values_by_substance.items())
    ]


def _timestamp_label(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, APP_ZONEINFO).isoformat(timespec="seconds")
