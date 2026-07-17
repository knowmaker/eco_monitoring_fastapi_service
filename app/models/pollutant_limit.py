from __future__ import annotations

from sqlalchemy import Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PollutantLimit(Base):
    __tablename__ = "pollutant_limits"

    pollutant_code: Mapped[str] = mapped_column(Text, primary_key=True)
    pdk_max_once: Mapped[float | None] = mapped_column(Float, nullable=True)
    pdk_daily: Mapped[float | None] = mapped_column(Float, nullable=True)
    pdk_annual: Mapped[float | None] = mapped_column(Float, nullable=True)
