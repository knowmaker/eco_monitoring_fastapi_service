from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_state import DeviceState
from app.models.ivtm_state import IvtmState
from app.models.plc_state import PlcState
from app.schemas.ivtm_state import IvtmStateHourlyResponse, IvtmStateHourPoint, IvtmStateMetricSeriesOut


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/ivtm_state", tags=["ivtm_state"])


@router.get("/hourly", response_model=IvtmStateHourlyResponse)
def get_hourly_ivtm_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> IvtmStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(IvtmState.device_timestamp_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            hour_expr.label("hour"),
            func.avg(IvtmState.sensor_ivtm_hum).label("sensor_ivtm_hum"),
            func.avg(IvtmState.sensor_ivtm_temp).label("sensor_ivtm_temp"),
        )
        .join(DeviceState, DeviceState.id == IvtmState.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            DeviceState.device_type == "ivtm",
            date_expr == day,
        )
        .group_by(hour_expr)
        .order_by(hour_expr.asc())
    ).all()

    by_hour: dict[int, dict[str, float | None]] = {}
    for row in rows:
        by_hour[int(row.hour)] = {
            "sensor_ivtm_hum": float(row.sensor_ivtm_hum) if row.sensor_ivtm_hum is not None else None,
            "sensor_ivtm_temp": float(row.sensor_ivtm_temp) if row.sensor_ivtm_temp is not None else None,
        }

    metric_labels = [
        ("sensor_ivtm_hum", "IVTM Humidity"),
        ("sensor_ivtm_temp", "IVTM Temperature"),
    ]
    series = []
    for key, label in metric_labels:
        points = [IvtmStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(IvtmStateMetricSeriesOut(key=key, label=label, points=points))

    return IvtmStateHourlyResponse(date=day.isoformat(), series=series)
