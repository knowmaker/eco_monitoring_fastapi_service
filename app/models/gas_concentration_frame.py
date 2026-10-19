from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasConcentrationFrame(Base):
    __tablename__ = "gas_concentration_frames"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    substance_code: Mapped[str] = mapped_column(Text, nullable=False)
    hour_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_kind: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, deferred=True)
    content_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    cell_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cell_size_meters: Mapped[int] = mapped_column(Integer, nullable=False)
    south: Mapped[float] = mapped_column(Float, nullable=False)
    west: Mapped[float] = mapped_column(Float, nullable=False)
    north: Mapped[float] = mapped_column(Float, nullable=False)
    east: Mapped[float] = mapped_column(Float, nullable=False)
    value_min: Mapped[float] = mapped_column(Float, nullable=False)
    value_max: Mapped[float] = mapped_column(Float, nullable=False)
    source_station_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
