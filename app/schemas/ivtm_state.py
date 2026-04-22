from pydantic import BaseModel


class IvtmStateHourPoint(BaseModel):
    hour: int
    value: float | None


class IvtmStateMetricSeriesOut(BaseModel):
    key: str
    label: str
    points: list[IvtmStateHourPoint]


class IvtmStateHourlyResponse(BaseModel):
    date: str
    series: list[IvtmStateMetricSeriesOut]
