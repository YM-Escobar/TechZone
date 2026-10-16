from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.Schema.auth_schema import (
    ForgotPasswordRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
    VerifyEmailRequest,
)
from app.Schema.common_schema import Message
from app.Schema.user_schema import UserCreate, UserOut
from app.Services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db: DbSession) -> AuthService:
    return AuthService(db)


Service = Annotated[AuthService, Depends(get_service)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, service: Service, background_tasks: BackgroundTasks):
    return service.register(data, background_tasks)


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], service: Service):
    """`username` acepta el correo o el nombre de usuario."""
    return service.login(form.username, form.password)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, service: Service):
    """Cambia un refresh token por un par nuevo; el anterior deja de servir."""
    return service.refresh(data.refresh_token)


@router.post("/logout", response_model=Message)
def logout(data: RefreshRequest, service: Service):
    service.logout(data.refresh_token)
    return Message(detail="Sesión cerrada")


@router.post("/logout-all", response_model=Message)
def logout_all(user: CurrentUser, service: Service):
    service.logout_all(user)
    return Message(detail="Se cerraron todas tus sesiones")


@router.post("/verify-email", response_model=UserOut)
def verify_email(data: VerifyEmailRequest, service: Service):
    return service.verify_email(data.token)


@router.post("/resend-verification", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
def resend_verification(user: CurrentUser, service: Service, background_tasks: BackgroundTasks):
    service.resend_verification(user, background_tasks)
    return Message(detail="Te enviamos un nuevo enlace de verificación")


@router.post("/forgot-password", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(data: ForgotPasswordRequest, service: Service, background_tasks: BackgroundTasks):
    service.request_password_reset(data.email, background_tasks)
    return Message(detail="Si el correo está registrado, recibirás un enlace para recuperar tu contraseña")


@router.post("/reset-password", response_model=Message)
def reset_password(data: ResetPasswordRequest, service: Service):
    service.reset_password(data.token, data.new_password)
    return Message(detail="Contraseña actualizada correctamente")
