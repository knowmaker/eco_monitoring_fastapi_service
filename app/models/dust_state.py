from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DustState(Base):
    __tablename__ = "dust_state"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm1_concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm2_concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10_concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsp_concentration: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[bool | None] = mapped_column(nullable=True)
