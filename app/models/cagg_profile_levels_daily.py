from __future__ import annotations

from sqlalchemy import BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggProfileLevelsDaily(Base):
    __tablename__ = "cagg_profile_levels_daily"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    height: Mapped[float] = mapped_column(Float, primary_key=True)
    temperature_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
