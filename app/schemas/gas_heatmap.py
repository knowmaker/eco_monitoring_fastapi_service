from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


HeatmapDataKind = Literal["observed", "forecast", "unavailable"]


class GasHeatmapPointOut(BaseModel):
    monitoring_post_id: int
    latitude: float
    longitude: float
    value: float
    lower_bound: float | None = None
    upper_bound: float | None = None


class GasHeatmapResponse(BaseModel):
    substance_code: str
    hour_start: datetime
    hour_end: datetime
    data_kind: HeatmapDataKind
    generated_at: datetime | None = None
    points: list[GasHeatmapPointOut] = Field(default_factory=list)


class GasHeatmapTimelineItemOut(BaseModel):
    hour_start: datetime
    data_kind: Literal["observed", "forecast"]
    available_points: int


class GasHeatmapTimelineResponse(BaseModel):
    substance_code: str
    current_hour: datetime
    items: list[GasHeatmapTimelineItemOut] = Field(default_factory=list)
