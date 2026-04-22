from pydantic import BaseModel


class GasStateLatestOut(BaseModel):
    device_state_id: int
    device_timestamp_ms: int
    board_temperature: float | None
    calibration_set_time_ms: int | None
    calibration_value: float | None
    calibration_time_start_ms: int | None
    calibration_time_end_ms: int | None
    calibration_warning: int | None
    calibration_status: str | None


class GasStateLatestResponse(BaseModel):
    gas_state: GasStateLatestOut | None
