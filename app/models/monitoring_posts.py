from __future__ import annotations

from sqlalchemy import Boolean, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonitoringPost(Base):
    __tablename__ = "monitoring_posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    serial: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_stationary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
