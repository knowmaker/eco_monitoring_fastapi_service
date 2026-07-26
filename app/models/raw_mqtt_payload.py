from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawMqttPayload(Base):
    __tablename__ = "raw_mqtt_payload"

    plc_state_id: Mapped[int] = mapped_column(
        ForeignKey("plc_state.id", ondelete="CASCADE"),
        primary_key=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
