from __future__ import annotations

from sqlalchemy import BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggDustHourly(Base):
    __tablename__ = "cagg_dust_hourly"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    humidity_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm1_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm2_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsp_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
