from __future__ import annotations

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProfileLevel(Base):
    __tablename__ = "profile_levels"

    device_state_id: Mapped[int] = mapped_column(
        ForeignKey("device_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    device_timestamp_ms: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    height: Mapped[float] = mapped_column(Float, primary_key=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
