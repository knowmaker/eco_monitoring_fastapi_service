from pydantic import BaseModel


class DustStateHourPoint(BaseModel):
    hour: int
    value: float | None


class DustStateDayPoint(BaseModel):
    day: int
    value: float | None


class DustStateRawPoint(BaseModel):
    timestamp: str
    value: float | None


class DustStateMetricSeriesOut(BaseModel):
    key: str
    points: list[DustStateHourPoint] | list[DustStateDayPoint]


class DustStateRawMetricSeriesOut(BaseModel):
    key: str
    points: list[DustStateRawPoint]


class DustStateHourlyResponse(BaseModel):
    date: str
    series: list[DustStateMetricSeriesOut]


class DustStateMonthlyResponse(BaseModel):
    month: str
    series: list[DustStateMetricSeriesOut]


class DustStateRawResponse(BaseModel):
    start: str
    end: str
    series: list[DustStateRawMetricSeriesOut]
