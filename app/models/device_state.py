from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeviceState(Base):
    __tablename__ = "device_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plc_state_id: Mapped[int] = mapped_column(ForeignKey("plc_state.id", ondelete="CASCADE"), nullable=False)
    device_type: Mapped[str] = mapped_column(Text, nullable=False)
    device_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    ping: Mapped[str | None] = mapped_column(Text, nullable=True)
    ping_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    device_timestamp_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    number_reboot_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    number_reboot_time_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
