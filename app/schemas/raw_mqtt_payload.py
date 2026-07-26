from typing import Any

from pydantic import BaseModel


class RawMqttPayloadRecordOut(BaseModel):
    packet: dict[str, Any]


class RawMqttPayloadResponse(BaseModel):
    monitoring_post_id: int
    date: str | None
    limit: int
    records: list[RawMqttPayloadRecordOut]
