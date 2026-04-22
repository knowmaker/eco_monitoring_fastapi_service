from pydantic import BaseModel


class PlcStateLatestOut(BaseModel):
    id: int
    monitoring_post_id: int
    aggregation_period_min: int
    plc_timestamp_ms: int
    received_at: str


class PlcStateLatestResponse(BaseModel):
    plc_state: PlcStateLatestOut | None
