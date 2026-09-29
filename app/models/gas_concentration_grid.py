from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasConcentrationGrid(Base):
    __tablename__ = "gas_concentration_grid"

    substance_code: Mapped[str] = mapped_column(Text, primary_key=True)
    hour_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    data_kind: Mapped[str] = mapped_column(Text, primary_key=True)
    cluster_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    grid_x: Mapped[int] = mapped_column(Integer, primary_key=True)
    grid_y: Mapped[int] = mapped_column(Integer, primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    south: Mapped[float] = mapped_column(Float, nullable=False)
    west: Mapped[float] = mapped_column(Float, nullable=False)
    north: Mapped[float] = mapped_column(Float, nullable=False)
    east: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    analysis_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_forecast: Mapped[float | None] = mapped_column(Float, nullable=True)
    correction_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_station_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_u: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    boundary_layer_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    diffusion_coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    decay_coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
