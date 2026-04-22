from pydantic import BaseModel


class GasSensorsHourPoint(BaseModel):
    hour: int
    value: float | None


class GasSensorsSubstanceSeriesOut(BaseModel):
    substance_code: str
    points: list[GasSensorsHourPoint]


class GasSensorsHourlyResponse(BaseModel):
    date: str
    substances: list[GasSensorsSubstanceSeriesOut]
