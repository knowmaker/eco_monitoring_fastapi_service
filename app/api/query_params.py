from fastapi import HTTPException

from app.core.dates import MonthPeriod, parse_local_datetime, parse_month


def parse_month_query(value: str | None) -> MonthPeriod:
    try:
        return parse_month(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def parse_datetime_query(value: str, *, is_end: bool):
    try:
        return parse_local_datetime(value, is_end=is_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def parse_datetime_range_query(start_value: str, end_value: str):
    start = parse_datetime_query(start_value, is_end=False)
    end = parse_datetime_query(end_value, is_end=True)
    if start >= end:
        raise HTTPException(status_code=422, detail="from must be earlier than to")
    return start, end
