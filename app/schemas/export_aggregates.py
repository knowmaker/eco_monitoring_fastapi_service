from typing import Literal

from pydantic import BaseModel, Field


DeviceType = Literal["gas", "dust", "meteo", "ivtm", "profile"]
AggregationType = Literal["hourly", "daily"]


class ExportAggregatesRequest(BaseModel):
    station_ids: list[int] | None = None
    device_types: list[DeviceType] = Field(min_length=1)
    aggregation: AggregationType
    start: str
    end: str
