from __future__ import annotations

from sqlalchemy import BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggProfileInversionHourly(Base):
    __tablename__ = "cagg_profile_inversion_hourly"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inversion_power_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    inversion_lower_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    inversion_upper_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
