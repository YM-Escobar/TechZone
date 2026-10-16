from __future__ import annotations

from sqlalchemy import func, or_, select

from app.Models.user import User, UserRole
from app.Repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def get_by_login(self, identifier: str) -> User | None:
        """Busca por correo o por nombre de usuario."""
        value = identifier.lower()
        return self.db.scalar(
            select(User).where(or_(func.lower(User.email) == value, func.lower(User.username) == value))
        )

    def list(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(
                User.email.ilike(pattern), User.username.ilike(pattern), User.full_name.ilike(pattern)
            ))
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        return self.paginate(stmt, skip, limit)

    def count_active_admins(self) -> int:
        return self.count(User.role == UserRole.ADMIN, User.is_active.is_(True))
