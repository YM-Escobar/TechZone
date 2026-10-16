from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.types import enum_column

if TYPE_CHECKING:
    from app.Models.advisory import AdvisoryRequest
    from app.Models.auth import AuthToken
    from app.Models.build import Build
    from app.Models.community import Comment, Post, PostLike, Report


class UserRole(StrEnum):
    USER = "usuario"
    ADVISOR = "asesor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole), default=UserRole.USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Al eliminar un usuario se elimina todo su contenido
    builds: Mapped[list["Build"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    advisory_requests: Mapped[list["AdvisoryRequest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", foreign_keys="AdvisoryRequest.user_id"
    )
    tokens: Mapped[list["AuthToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(
        back_populates="reporter", cascade="all, delete-orphan", foreign_keys="Report.reporter_id"
    )

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_staff(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.ADVISOR)
