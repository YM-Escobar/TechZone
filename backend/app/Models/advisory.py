from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.types import enum_column
from app.Models.build import Build
from app.Models.user import User


class AdvisoryPurpose(StrEnum):
    GAMING = "gaming"
    OFFICE = "oficina"
    DESIGN = "diseno"
    VIDEO_EDITING = "edicion_video"
    STREAMING = "streaming"
    PROGRAMMING = "programacion"
    OTHER = "otro"


class AdvisoryStatus(StrEnum):
    PENDING = "pendiente"
    IN_PROGRESS = "en_progreso"
    COMPLETED = "completada"
    CANCELLED = "cancelada"


class AdvisoryRequest(Base):
    """Solicitud de asesoría personalizada: un usuario pide una recomendación y un asesor responde."""

    __tablename__ = "advisory_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    advisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    purpose: Mapped[AdvisoryPurpose] = mapped_column(enum_column(AdvisoryPurpose))
    budget: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    preferences: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AdvisoryStatus] = mapped_column(
        enum_column(AdvisoryStatus), default=AdvisoryStatus.PENDING, index=True
    )
    advisor_notes: Mapped[str | None] = mapped_column(Text)
    recommended_build_id: Mapped[int | None] = mapped_column(ForeignKey("builds.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(
        back_populates="advisory_requests", foreign_keys=[user_id], lazy="joined"
    )
    advisor: Mapped[User | None] = relationship(foreign_keys=[advisor_id], lazy="joined")
    recommended_build: Mapped[Build | None] = relationship(lazy="selectin")
