from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_dust_hourly import CaggDustHourly
from app.schemas.dust_state import DustStateHourlyResponse, DustStateHourPoint, DustStateMetricSeriesOut


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/dust_state", tags=["dust_state"])


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
            CaggDustHourly.humidity_avg.label("humidity"),
            CaggDustHourly.temp_avg.label("temp"),
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
            "humidity": float(row.humidity) if row.humidity is not None else None,
            "temp": float(row.temp) if row.temp is not None else None,
            "pm1_concentration": float(row.pm1_concentration) if row.pm1_concentration is not None else None,
            "pm2_concentration": float(row.pm2_concentration) if row.pm2_concentration is not None else None,
            "pm10_concentration": float(row.pm10_concentration) if row.pm10_concentration is not None else None,
            "tsp_concentration": float(row.tsp_concentration) if row.tsp_concentration is not None else None,
        }

    metric_labels = [
        ("humidity", "Humidity"),
        ("temp", "Temperature"),
        ("pm1_concentration", "PM1"),
        ("pm2_concentration", "PM2.5"),
        ("pm10_concentration", "PM10"),
        ("tsp_concentration", "TSP"),
    ]
    series = []
    for key, label in metric_labels:
        points = [DustStateHourPoint(hour=h, value=by_hour.get(h, {}).get(key)) for h in range(24)]
        series.append(DustStateMetricSeriesOut(key=key, label=label, points=points))

    return DustStateHourlyResponse(date=day.isoformat(), series=series)
