from datetime import datetime, timezone

from sqlalchemy import select, update

from app.Models.auth import AuthToken, TokenPurpose
from app.Repository.base_repository import BaseRepository


class AuthTokenRepository(BaseRepository[AuthToken]):
    model = AuthToken

    def get_by_hash(self, token_hash: str, purpose: TokenPurpose) -> AuthToken | None:
        return self.db.scalar(
            select(AuthToken).where(AuthToken.token_hash == token_hash, AuthToken.purpose == purpose)
        )

    def invalidate_for_user(self, user_id: int, purpose: TokenPurpose) -> None:
        """Marca como usados los tokens pendientes de ese tipo (p. ej. cerrar todas las sesiones)."""
        self.db.execute(
            update(AuthToken)
            .where(AuthToken.user_id == user_id, AuthToken.purpose == purpose, AuthToken.used_at.is_(None))
            .values(used_at=datetime.now(timezone.utc))
        )
        self.db.commit()
