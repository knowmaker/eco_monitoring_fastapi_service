from pydantic import BaseModel


class MeteoStateHourPoint(BaseModel):
    hour: int
    value: float | None


class MeteoStateDayPoint(BaseModel):
    day: int
    value: float | None


class MeteoStateMetricSeriesOut(BaseModel):
    key: str
    points: list[MeteoStateHourPoint] | list[MeteoStateDayPoint]


class MeteoStateHourlyResponse(BaseModel):
    date: str
    series: list[MeteoStateMetricSeriesOut]


class MeteoStateMonthlyResponse(BaseModel):
    month: str
    series: list[MeteoStateMetricSeriesOut]
