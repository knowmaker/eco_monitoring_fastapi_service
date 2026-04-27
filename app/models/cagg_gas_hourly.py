from __future__ import annotations

from sqlalchemy import BigInteger, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggGasHourly(Base):
    __tablename__ = "cagg_gas_hourly"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    substance_code: Mapped[str] = mapped_column(Text, primary_key=True)
    value_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
