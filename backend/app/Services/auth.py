from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, generate_token, hash_password, hash_token, verify_password
from app.Models.auth import AuthToken, TokenPurpose
from app.Models.user import User, UserRole
from app.Repository.auth_repository import AuthTokenRepository
from app.Repository.user_repository import UserRepository
from app.Schema.auth_schema import Token
from app.Schema.user_schema import UserCreate
from app.Services import mailer

TOKEN_TTL = {
    TokenPurpose.REFRESH: timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    TokenPurpose.PASSWORD_RESET: timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    TokenPurpose.EMAIL_VERIFICATION: timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
}


def ensure_user_unique(
    users: UserRepository, *, email: str | None = None, username: str | None = None, exclude_id: int | None = None
) -> None:
    if email:
        existing = users.get_by_email(email)
        if existing and existing.id != exclude_id:
            raise ConflictError("Ya existe una cuenta con ese correo")
    if username:
        existing = users.get_by_username(username)
        if existing and existing.id != exclude_id:
            raise ConflictError("Ese nombre de usuario ya está en uso")


def create_user(
    users: UserRepository, data: UserCreate, role: UserRole = UserRole.USER, is_verified: bool = False
) -> User:
    email = data.email.lower()
    ensure_user_unique(users, email=email, username=data.username)
    return users.add(User(
        email=email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=role,
        is_verified=is_verified,
    ))


def _as_utc(value: datetime) -> datetime:
    # SQLite devuelve fechas sin zona horaria; PostgreSQL las devuelve con zona
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.tokens = AuthTokenRepository(db)

    # Registro y sesión

    def register(self, data: UserCreate, background_tasks: BackgroundTasks | None = None) -> User:
        user = create_user(self.users, data)
        self._send_verification(user, background_tasks)
        return user

    def login(self, identifier: str, password: str) -> Token:
        user = self.users.get_by_login(identifier.strip())
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Correo/usuario o contraseña incorrectos")
        if not user.is_active:
            raise ForbiddenError("Tu cuenta está desactivada")
        return self._issue_session(user)

    def refresh(self, refresh_token: str) -> Token:
        stored = self.tokens.get_by_hash(hash_token(refresh_token), TokenPurpose.REFRESH)
        if stored is not None and stored.used_at is not None:
            # Reutilizar un refresh token ya rotado indica que pudo ser robado: se cierran todas las sesiones
            self.tokens.invalidate_for_user(stored.user_id, TokenPurpose.REFRESH)
            raise UnauthorizedError("La sesión expiró, inicia sesión de nuevo")

        stored = self._consume(refresh_token, TokenPurpose.REFRESH, "La sesión expiró, inicia sesión de nuevo",
                               error=UnauthorizedError)
        if not stored.user.is_active:
            raise ForbiddenError("Tu cuenta está desactivada")
        return self._issue_session(stored.user)

    def logout(self, refresh_token: str) -> None:
        stored = self.tokens.get_by_hash(hash_token(refresh_token), TokenPurpose.REFRESH)
        if stored is not None and stored.used_at is None:
            stored.used_at = datetime.now(timezone.utc)
            self.tokens.save(stored)

    def logout_all(self, user: User) -> None:
        self.tokens.invalidate_for_user(user.id, TokenPurpose.REFRESH)

    # Verificación de correo

    def verify_email(self, token: str) -> User:
        stored = self._consume(token, TokenPurpose.EMAIL_VERIFICATION, "El enlace de verificación es inválido o ya expiró")
        stored.user.is_verified = True
        return self.users.save(stored.user)

    def resend_verification(self, user: User, background_tasks: BackgroundTasks | None = None) -> None:
        if user.is_verified:
            raise ConflictError("Tu correo ya está verificado")
        self._send_verification(user, background_tasks)

    # Recuperación de contraseña

    def request_password_reset(self, email: str, background_tasks: BackgroundTasks | None = None) -> None:
        user = self.users.get_by_email(email)
        # No se revela si el correo existe o no
        if user is None or not user.is_active:
            return
        self.tokens.invalidate_for_user(user.id, TokenPurpose.PASSWORD_RESET)
        token = self._issue(user, TokenPurpose.PASSWORD_RESET)
        mailer.send_password_reset_email(background_tasks, user, token)

    def reset_password(self, token: str, new_password: str) -> None:
        stored = self._consume(token, TokenPurpose.PASSWORD_RESET, "El enlace de recuperación es inválido o ya expiró")
        stored.user.hashed_password = hash_password(new_password)
        self.users.save(stored.user)
        # Al cambiar la contraseña se cierran las sesiones abiertas
        self.tokens.invalidate_for_user(stored.user_id, TokenPurpose.REFRESH)

    # Auxiliares

    def _issue_session(self, user: User) -> Token:
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=self._issue(user, TokenPurpose.REFRESH),
        )

    def _issue(self, user: User, purpose: TokenPurpose) -> str:
        token, token_hash = generate_token()
        self.tokens.add(AuthToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + TOKEN_TTL[purpose],
        ))
        return token

    def _consume(
        self, token: str, purpose: TokenPurpose, message: str, error: type[Exception] = BadRequestError
    ) -> AuthToken:
        """Valida un token y lo marca como usado (cada token sirve una sola vez)."""
        stored = self.tokens.get_by_hash(hash_token(token), purpose)
        now = datetime.now(timezone.utc)
        if stored is None or stored.used_at is not None or _as_utc(stored.expires_at) < now:
            raise error(message)
        stored.used_at = now
        return self.tokens.save(stored)

    def _send_verification(self, user: User, background_tasks: BackgroundTasks | None) -> None:
        self.tokens.invalidate_for_user(user.id, TokenPurpose.EMAIL_VERIFICATION)
        token = self._issue(user, TokenPurpose.EMAIL_VERIFICATION)
        mailer.send_verification_email(background_tasks, user, token)
