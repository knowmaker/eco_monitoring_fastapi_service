from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_meteo_hourly import CaggMeteoHourly
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
