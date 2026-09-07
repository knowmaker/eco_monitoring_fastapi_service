from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileState(Base):
    __tablename__ = "profile_state"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    inversion_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    inversion_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    inversion_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    inversion_delta_t: Mapped[float | None] = mapped_column(Float, nullable=True)
