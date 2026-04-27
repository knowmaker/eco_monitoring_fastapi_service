from __future__ import annotations

from sqlalchemy import BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaggMeteoHourly(Base):
    __tablename__ = "cagg_meteo_hourly"

    bucket_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    atm_press_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_temp_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    air_hum_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hor_win_dir_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hor_win_spd_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
