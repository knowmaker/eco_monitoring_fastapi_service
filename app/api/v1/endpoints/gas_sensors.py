from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cagg_gas_hourly import CaggGasHourly
from app.schemas.gas_sensors import GasSensorsHourPoint, GasSensorsHourlyResponse, GasSensorsSubstanceSeriesOut


APP_TIMEZONE = "Europe/Moscow"

router = APIRouter(prefix="/gas_sensors", tags=["gas_sensors"])


@router.get("/hourly", response_model=GasSensorsHourlyResponse)
def get_hourly_gas_sensors(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> GasSensorsHourlyResponse:
    day = target_date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()

    local_ts = func.timezone(APP_TIMEZONE, func.to_timestamp(CaggGasHourly.bucket_ms / 1000.0))
    hour_expr = cast(func.extract("hour", local_ts), Integer)
    date_expr = cast(local_ts, Date)

    rows = db.execute(
        select(
            CaggGasHourly.substance_code.label("substance_code"),
            hour_expr.label("hour"),
            CaggGasHourly.value_avg.label("value"),
        )
        .where(
            CaggGasHourly.monitoring_post_id == monitoring_post_id,
            date_expr == day,
        )
        .order_by(CaggGasHourly.substance_code.asc(), hour_expr.asc())
    ).all()

    values_by_substance: dict[str, dict[int, float | None]] = {}
    for substance_code, hour, value in rows:
        substance_key = str(substance_code)
        if substance_key not in values_by_substance:
            values_by_substance[substance_key] = {}
        values_by_substance[substance_key][int(hour)] = float(value) if value is not None else None

    substances = []
    for substance_code in sorted(values_by_substance.keys()):
        by_hour = values_by_substance[substance_code]
        points = [GasSensorsHourPoint(hour=h, value=by_hour.get(h)) for h in range(24)]
        substances.append(GasSensorsSubstanceSeriesOut(substance_code=substance_code, points=points))

    return GasSensorsHourlyResponse(date=day.isoformat(), substances=substances)
