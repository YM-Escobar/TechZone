from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.Models.auth import TokenPurpose
from app.Models.user import User
from app.Repository.auth_repository import AuthTokenRepository
from app.Repository.user_repository import UserRepository
from app.Schema.common_schema import update_data
from app.Schema.user_schema import PasswordChange, UserUpdate
from app.Services import storage
from app.Services.auth import ensure_user_unique

PROFILE_NULLABLE = {"full_name", "bio", "avatar_url"}


class ProfileService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.tokens = AuthTokenRepository(db)

    def update(self, user: User, data: UserUpdate) -> User:
        changes = update_data(data, PROFILE_NULLABLE)
        if "username" in changes:
            ensure_user_unique(self.users, username=changes["username"], exclude_id=user.id)
        if "avatar_url" in changes and changes["avatar_url"] != user.avatar_url:
            storage.delete_image(user.avatar_url)
        for field, value in changes.items():
            setattr(user, field, value)
        return self.users.save(user)

    def set_avatar(self, user: User, content: bytes) -> User:
        new_url = storage.save_image(content, "avatars")
        storage.delete_image(user.avatar_url)
        user.avatar_url = new_url
        return self.users.save(user)

    def remove_avatar(self, user: User) -> User:
        storage.delete_image(user.avatar_url)
        user.avatar_url = None
        return self.users.save(user)

    def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestError("La contraseña actual es incorrecta")
        if data.current_password == data.new_password:
            raise BadRequestError("La nueva contraseña debe ser diferente a la actual")
        user.hashed_password = hash_password(data.new_password)
        self.users.save(user)
        # Cierra las sesiones abiertas en otros dispositivos
        self.tokens.invalidate_for_user(user.id, TokenPurpose.REFRESH)

    def delete_account(self, user: User) -> None:
        if user.is_admin and self.users.count_active_admins() <= 1:
            raise ConflictError("No puedes eliminar la única cuenta de administrador")
        avatar_url = user.avatar_url
        self.users.delete(user)
        storage.delete_image(avatar_url)

    def get_public_profile(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise NotFoundError("Usuario no encontrado")
        return user
