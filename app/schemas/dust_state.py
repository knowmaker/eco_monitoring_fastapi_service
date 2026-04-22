from pydantic import BaseModel


class DustStateHourPoint(BaseModel):
    hour: int
    value: float | None


class DustStateMetricSeriesOut(BaseModel):
    key: str
    label: str
    points: list[DustStateHourPoint]


class DustStateHourlyResponse(BaseModel):
    date: str
    series: list[DustStateMetricSeriesOut]
