from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ConcentrationMapDataKind = Literal["observed", "forecast", "unavailable"]


class ConcentrationMapBoundsOut(BaseModel):
    south: float
    west: float
    north: float
    east: float


class ConcentrationMapResponse(BaseModel):
    substance_code: str
    pdk_max_once: float | None = None
    hour_start: datetime
    hour_end: datetime
    data_kind: ConcentrationMapDataKind
    generated_at: datetime | None = None
    source_station_count: int = 0
    wind_speed: float | None = None
    wind_direction: float | None = None
    cell_count: int = 0
    cell_size_meters: int | None = None
    value_min: float | None = None
    value_max: float | None = None
    bounds: ConcentrationMapBoundsOut | None = None
    tile_url: str | None = None


class ConcentrationMapValueResponse(BaseModel):
    substance_code: str
    hour_start: datetime
    data_kind: Literal["observed", "forecast"]
    latitude: float
    longitude: float
    value: float | None = None


class ConcentrationMapTimelineItemOut(BaseModel):
    hour_start: datetime
    data_kind: Literal["observed", "forecast"]
    cell_count: int


class ConcentrationMapTimelineResponse(BaseModel):
    substance_code: str
    current_hour: datetime
    items: list[ConcentrationMapTimelineItemOut] = Field(default_factory=list)
