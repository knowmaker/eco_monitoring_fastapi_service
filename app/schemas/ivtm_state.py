from pydantic import BaseModel


class IvtmStateHourPoint(BaseModel):
    hour: int
    value: float | None


class IvtmStateDayPoint(BaseModel):
    day: int
    value: float | None


class IvtmStateRawPoint(BaseModel):
    timestamp: str
    value: float | None


class IvtmStateMetricSeriesOut(BaseModel):
    key: str
    points: list[IvtmStateHourPoint] | list[IvtmStateDayPoint]


class IvtmStateRawMetricSeriesOut(BaseModel):
    key: str
    points: list[IvtmStateRawPoint]


class IvtmStateHourlyResponse(BaseModel):
    date: str
    series: list[IvtmStateMetricSeriesOut]


class IvtmStateMonthlyResponse(BaseModel):
    month: str
    series: list[IvtmStateMetricSeriesOut]


class IvtmStateRawResponse(BaseModel):
    start: str
    end: str
    series: list[IvtmStateRawMetricSeriesOut]
