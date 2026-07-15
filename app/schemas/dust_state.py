from pydantic import BaseModel


class DustStateHourPoint(BaseModel):
    hour: int
    value: float | None


class DustStateDayPoint(BaseModel):
    day: int
    value: float | None


class DustStateMetricSeriesOut(BaseModel):
    key: str
    points: list[DustStateHourPoint] | list[DustStateDayPoint]


class DustStateHourlyResponse(BaseModel):
    date: str
    series: list[DustStateMetricSeriesOut]


class DustStateMonthlyResponse(BaseModel):
    month: str
    series: list[DustStateMetricSeriesOut]
