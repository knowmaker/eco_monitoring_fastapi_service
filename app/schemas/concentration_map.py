from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ConcentrationMapDataKind = Literal["observed", "forecast", "unavailable"]


class ConcentrationMapCellOut(BaseModel):
    latitude: float
    longitude: float
    south: float
    west: float
    north: float
    east: float
    value: float
    confidence: float
    lower_bound: float | None = None
    upper_bound: float | None = None


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
    cells: list[ConcentrationMapCellOut] = Field(default_factory=list)


class ConcentrationMapTimelineItemOut(BaseModel):
    hour_start: datetime
    data_kind: Literal["observed", "forecast"]
    available_cells: int


class ConcentrationMapTimelineResponse(BaseModel):
    substance_code: str
    current_hour: datetime
    items: list[ConcentrationMapTimelineItemOut] = Field(default_factory=list)
