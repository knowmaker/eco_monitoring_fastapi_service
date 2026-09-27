from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasHourlyFeature(Base):
    __tablename__ = "gas_hourly_features"

    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    substance_code: Mapped[str] = mapped_column(Text, primary_key=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    raw_hourly_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_hourly_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    filtered_hourly_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_p95: Mapped[float | None] = mapped_column(Float, nullable=True)
    hourly_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    samples_count: Mapped[int] = mapped_column(Integer, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
