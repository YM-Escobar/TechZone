from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Query, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.Models.user import User, UserRole
from app.Repository.user_repository import UserRepository
from app.Services.storage import max_upload_bytes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def _user_from_token(db: Session, token: str) -> User:
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Token inválido o expirado")

    user = UserRepository(db).get(user_id)
    if user is None:
        raise UnauthorizedError("Token inválido o expirado")
    if not user.is_active:
        raise ForbiddenError("Tu cuenta está desactivada")
    return user


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    return _user_from_token(db, token)


def get_optional_user(
    db: DbSession, token: Annotated[str | None, Depends(oauth2_scheme_optional)]
) -> User | None:
    """Para rutas públicas que muestran más información si hay sesión iniciada."""
    return _user_from_token(db, token) if token else None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def get_verified_user(user: CurrentUser) -> User:
    """Para crear contenido; solo exige correo verificado si REQUIRE_EMAIL_VERIFICATION está activo."""
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified and not user.is_staff:
        raise ForbiddenError("Debes verificar tu correo para realizar esta acción")
    return user


VerifiedUser = Annotated[User, Depends(get_verified_user)]


def require_roles(*roles: UserRole):
    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError("No tienes permisos para realizar esta acción")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.ADVISOR))]


@dataclass
class Pagination:
    skip: int
    limit: int


def get_pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagination:
    return Pagination(skip, limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]


def read_upload(file: UploadFile) -> bytes:
    # Se lee un byte más del límite para que el service detecte archivos demasiado grandes
    return file.file.read(max_upload_bytes() + 1)
