from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasState(Base):
    __tablename__ = "gas_state"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    board_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_set_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    calibration_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    calibration_time_start_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    calibration_time_end_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    calibration_warning: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calibration_status: Mapped[str | None] = mapped_column(Text, nullable=True)
