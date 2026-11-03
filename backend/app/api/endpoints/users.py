from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status

from app.api.deps import CurrentUser, DbSession, read_upload
from app.Schema.common_schema import Message
from app.Schema.user_schema import PasswordChange, UserOut, UserPublic, UserUpdate
from app.Services.profile import ProfileService

router = APIRouter(prefix="/users", tags=["perfil"])


def get_service(db: DbSession) -> ProfileService:
    return ProfileService(db)


Service = Annotated[ProfileService, Depends(get_service)]


@router.get("/me", response_model=UserOut)
def read_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, user: CurrentUser, service: Service):
    return service.update(user, data)


@router.put("/me/avatar", response_model=UserOut)
def upload_avatar(file: UploadFile, user: CurrentUser, service: Service):
    """Imagen JPG, PNG, WEBP o GIF; se sirve desde la URL guardada en `avatar_url`."""
    return service.set_avatar(user, read_upload(file))


@router.delete("/me/avatar", response_model=UserOut)
def delete_avatar(user: CurrentUser, service: Service):
    return service.remove_avatar(user)


@router.put("/me/password", response_model=Message)
def change_password(data: PasswordChange, user: CurrentUser, service: Service):
    service.change_password(user, data)
    return Message(detail="Contraseña actualizada correctamente")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, service: Service):
    service.delete_account(user)


@router.get("/{user_id}", response_model=UserPublic)
def read_public_profile(user_id: int, service: Service):
    return service.get_public_profile(user_id)
