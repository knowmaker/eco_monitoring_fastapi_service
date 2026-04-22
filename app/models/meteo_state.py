from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MeteoState(Base):
    __tablename__ = "meteo_state"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    atm_press: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_hum: Mapped[float | None] = mapped_column(Float, nullable=True)
    hor_win_dir: Mapped[float | None] = mapped_column(Float, nullable=True)
    hor_win_spd: Mapped[float | None] = mapped_column(Float, nullable=True)
