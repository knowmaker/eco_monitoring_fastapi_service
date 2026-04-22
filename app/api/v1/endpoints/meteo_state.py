from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, case, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_state import DeviceState
from app.models.meteo_state import MeteoState
from app.models.plc_state import PlcState
from app.schemas.meteo_state import MeteoStateHourlyResponse, MeteoStateHourPoint, MeteoStateMetricSeriesOut


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/meteo_state", tags=["meteo_state"])


@router.get("/hourly", response_model=MeteoStateHourlyResponse)
def get_hourly_meteo_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> MeteoStateHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(MeteoState.device_timestamp_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)
    wind_dir_rad = func.radians(MeteoState.hor_win_dir)
    wind_sin_avg = func.avg(func.sin(wind_dir_rad))
    wind_cos_avg = func.avg(func.cos(wind_dir_rad))
    wind_vector_len = func.sqrt(func.power(wind_sin_avg, 2) + func.power(wind_cos_avg, 2))
    wind_dir_avg = case(
        (wind_vector_len < 1e-6, None),
        else_=func.mod(func.degrees(func.atan2(wind_sin_avg, wind_cos_avg)) + 360.0, 360.0),
    )

    rows = db.execute(
        select(
            hour_expr.label("hour"),
            func.avg(MeteoState.atm_press).label("atm_press"),
            func.avg(MeteoState.air_temp).label("air_temp"),
            func.avg(MeteoState.air_hum).label("air_hum"),
            wind_dir_avg.label("hor_win_dir"),
            func.avg(MeteoState.hor_win_spd).label("hor_win_spd"),
        )
        .join(DeviceState, DeviceState.id == MeteoState.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            DeviceState.device_type == "meteo",
            date_expr == day,
        )
        .group_by(hour_expr)
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

    metric_labels = [
        ("atm_press", "Pressure"),
        ("air_temp", "Air Temperature"),
        ("air_hum", "Air Humidity"),
        ("hor_win_dir", "Wind Direction"),
        ("hor_win_spd", "Wind Speed"),
    ]
    series = []
    for key, label in metric_labels:
        points = [MeteoStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(MeteoStateMetricSeriesOut(key=key, label=label, points=points))

    return MeteoStateHourlyResponse(date=day.isoformat(), series=series)
