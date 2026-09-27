from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GasPrediction(Base):
    __tablename__ = "gas_predictions"

    monitoring_post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    substance_code: Mapped[str] = mapped_column(Text, primary_key=True)
    target_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    target_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
