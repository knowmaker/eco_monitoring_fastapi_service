from pydantic import BaseModel


class GasSensorsHourPoint(BaseModel):
    hour: int
    value: float | None


class GasSensorsDayPoint(BaseModel):
    day: int
    value: float | None


class GasSensorsSubstanceSeriesOut(BaseModel):
    substance_code: str
    points: list[GasSensorsHourPoint] | list[GasSensorsDayPoint]


class GasSensorsHourlyResponse(BaseModel):
    date: str
    substances: list[GasSensorsSubstanceSeriesOut]


class GasSensorsMonthlyResponse(BaseModel):
    month: str
    substances: list[GasSensorsSubstanceSeriesOut]
