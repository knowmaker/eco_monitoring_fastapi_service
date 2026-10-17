from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MosecomProfileHourly(Base):
    __tablename__ = "mosecom_profile_hourly"

    monitoring_post_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_posts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    height: Mapped[float] = mapped_column(Float, primary_key=True)
    temperature_avg: Mapped[float] = mapped_column("temperature", Float, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
