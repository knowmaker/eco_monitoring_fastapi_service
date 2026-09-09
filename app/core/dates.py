import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


APP_TIMEZONE = "Europe/Moscow"
APP_ZONEINFO = ZoneInfo(APP_TIMEZONE)


@dataclass(frozen=True)
class MonthPeriod:
    year: int
    month: int
    key: str
    days_count: int


def current_local_date() -> date:
    return datetime.now(APP_ZONEINFO).date()


def parse_month(value: str | None) -> MonthPeriod:
    if value is None:
        now = datetime.now(APP_ZONEINFO)
        year, month = now.year, now.month
    else:
        try:
            year_text, month_text = value.split("-", 1)
            year, month = int(year_text), int(month_text)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError as exc:
            raise ValueError("month must use YYYY-MM format") from exc

    return MonthPeriod(
        year=year,
        month=month,
        key=f"{year:04d}-{month:02d}",
        days_count=calendar.monthrange(year, month)[1],
    )


def parse_local_datetime(value: str, *, is_end: bool) -> datetime:
    text = value.strip()
    try:
        if len(text) == 10:
            parsed_date = date.fromisoformat(text)
            parsed = datetime.combine(parsed_date, time.max if is_end else time.min)
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("start and end must use ISO date or datetime format") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=APP_ZONEINFO)
    return parsed.astimezone(APP_ZONEINFO)


def to_epoch_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def local_day_bounds_ms(day: date) -> tuple[int, int]:
    start = datetime.combine(day, time.min, tzinfo=APP_ZONEINFO)
    end = start + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def bucket_label(bucket_ms: int, aggregation: str) -> str:
    local_dt = datetime.fromtimestamp(bucket_ms / 1000, APP_ZONEINFO)
    if aggregation == "daily":
        return local_dt.strftime("%Y-%m-%d")
    end_dt = local_dt.replace(minute=59, second=0, microsecond=0)
    return f"{local_dt:%Y-%m-%d %H:00}-{end_dt:%H:%M}"
