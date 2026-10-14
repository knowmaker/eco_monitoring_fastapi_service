from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MosecomHourlyReading(Base):
    __tablename__ = "mosecom_hourly_readings"

    monitoring_post_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_posts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    substance_code: Mapped[str] = mapped_column(Text, primary_key=True)
    value_avg: Mapped[float] = mapped_column("value", Float, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    pdk_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
