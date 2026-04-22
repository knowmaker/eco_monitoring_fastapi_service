from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.device_state import DeviceState
from app.models.gas_state import GasState
from app.models.plc_state import PlcState
from app.schemas.gas_state import GasStateLatestOut, GasStateLatestResponse


router = APIRouter(prefix="/gas_state", tags=["gas_state"])


@router.get("/latest", response_model=GasStateLatestResponse)
def get_latest_gas_state(
    monitoring_post_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> GasStateLatestResponse:
    row = db.scalar(
        select(GasState)
        .join(DeviceState, DeviceState.id == GasState.device_state_id)
        .join(PlcState, PlcState.id == DeviceState.plc_state_id)
        .where(
            PlcState.monitoring_post_id == monitoring_post_id,
            DeviceState.device_type == "gas",
        )
        .order_by(GasState.device_timestamp_ms.desc(), GasState.device_state_id.desc())
        .limit(1)
    )
    if row is None:
        return GasStateLatestResponse(gas_state=None)

    return GasStateLatestResponse(
        gas_state=GasStateLatestOut(
            device_state_id=row.device_state_id,
            device_timestamp_ms=row.device_timestamp_ms,
            board_temperature=row.board_temperature,
            calibration_set_time_ms=row.calibration_set_time_ms,
            calibration_value=row.calibration_value,
            calibration_time_start_ms=row.calibration_time_start_ms,
            calibration_time_end_ms=row.calibration_time_end_ms,
            calibration_warning=row.calibration_warning,
            calibration_status=row.calibration_status,
        )
    )
