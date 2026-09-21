from pydantic import BaseModel


class MeteoStateHourPoint(BaseModel):
    hour: int
    value: float | None


class MeteoStateDayPoint(BaseModel):
    day: int
    value: float | None


class MeteoStateRawPoint(BaseModel):
    timestamp: str
    value: float | None


class MeteoStateMetricSeriesOut(BaseModel):
    key: str
    points: list[MeteoStateHourPoint] | list[MeteoStateDayPoint]


class MeteoStateRawMetricSeriesOut(BaseModel):
    key: str
    points: list[MeteoStateRawPoint]


class MeteoStateHourlyResponse(BaseModel):
    date: str
    series: list[MeteoStateMetricSeriesOut]


class MeteoStateMonthlyResponse(BaseModel):
    month: str
    series: list[MeteoStateMetricSeriesOut]


class MeteoStateRawResponse(BaseModel):
    start: str
    end: str
    series: list[MeteoStateRawMetricSeriesOut]
