from __future__ import annotations

from sqlalchemy import ARRAY, BigInteger, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IvtmState(Base):
    __tablename__ = "ivtm_state"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_ivtm_hum: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_ivtm_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_ivtm_error: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
