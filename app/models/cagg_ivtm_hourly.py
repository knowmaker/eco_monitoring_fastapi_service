from __future__ import annotations

from sqlalchemy import BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggIvtmHourly(Base):
    __tablename__ = "cagg_ivtm_hourly"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_ivtm_hum_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_ivtm_temp_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
