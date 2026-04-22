from pydantic import BaseModel


class MeteoStateHourPoint(BaseModel):
    hour: int
    value: float | None


class MeteoStateMetricSeriesOut(BaseModel):
    key: str
    label: str
    points: list[MeteoStateHourPoint]


class MeteoStateHourlyResponse(BaseModel):
    date: str
    series: list[MeteoStateMetricSeriesOut]
