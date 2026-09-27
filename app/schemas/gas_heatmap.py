from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


HeatmapDataKind = Literal["observed", "forecast", "unavailable"]


class GasHeatmapCellOut(BaseModel):
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


class GasHeatmapResponse(BaseModel):
    substance_code: str
    hour_start: datetime
    hour_end: datetime
    data_kind: HeatmapDataKind
    generated_at: datetime | None = None
    source_station_count: int = 0
    wind_speed: float | None = None
    wind_direction: float | None = None
    cells: list[GasHeatmapCellOut] = Field(default_factory=list)


class GasHeatmapTimelineItemOut(BaseModel):
    hour_start: datetime
    data_kind: Literal["observed", "forecast"]
    available_cells: int


class GasHeatmapTimelineResponse(BaseModel):
    substance_code: str
    current_hour: datetime
    items: list[GasHeatmapTimelineItemOut] = Field(default_factory=list)
