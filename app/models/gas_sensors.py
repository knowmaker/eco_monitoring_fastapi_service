from __future__ import annotations

from sqlalchemy import BigInteger, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasSensors(Base):
    __tablename__ = "gas_sensors"

    device_state_id: Mapped[int] = mapped_column(primary_key=True)
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    substance_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    scale_dimension: Mapped[str | None] = mapped_column(Text, nullable=True)
    signal: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sensor_status: Mapped[str | None] = mapped_column(Text, nullable=True)
