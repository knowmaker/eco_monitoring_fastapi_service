from fastapi import HTTPException

from app.core.dates import MonthPeriod, parse_month


def parse_month_query(value: str | None) -> MonthPeriod:
    try:
        return parse_month(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
