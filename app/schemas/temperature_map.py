from datetime import datetime

from pydantic import BaseModel

from app.schemas.profile_state import ProfileInversionOut


class TemperatureMapLevelOut(BaseModel):
    height: float
    temperature: float


class TemperatureMapStationOut(BaseModel):
    monitoring_post_id: int
    name: str | None
    serial: str
    source: str
    device_type: str
    latitude: float
    longitude: float
    levels: list[TemperatureMapLevelOut]
    inversion: ProfileInversionOut | None = None


class TemperatureMapResponse(BaseModel):
    hour_start: datetime
    hour_end: datetime
    station_count: int
    min_temperature: float | None
    max_temperature: float | None
    stations: list[TemperatureMapStationOut]
