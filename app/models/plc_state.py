from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlcState(Base):
    __tablename__ = "plc_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    monitoring_post_id: Mapped[int] = mapped_column(ForeignKey("monitoring_posts.id"), nullable=False)
    aggregation_period_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    plc_timestamp_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    device_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
