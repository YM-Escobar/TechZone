
import logging
from typing import TYPE_CHECKING

import resend
from fastapi import BackgroundTasks

from app.core.config import settings

if TYPE_CHECKING:
    from app.Models.advisory import AdvisoryRequest
    from app.Models.user import User

logger = logging.getLogger("techzone.mailer")


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.warning(
            "Resend no configurado. Correo para %s | %s",
            to,
            subject,
        )
        return

    try:
        resend.api_key = settings.RESEND_API_KEY

        params = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "text": body,
        }

        response = resend.Emails.send(params)

        logger.info(
            "Correo enviado correctamente a %s. ID: %s",
            to,
            response.get("id") if isinstance(response, dict) else response,
        )

    except Exception:
        logger.exception("No se pudo enviar el correo a %s", to)


def _dispatch(
    background_tasks: BackgroundTasks | None,
    to: str,
    subject: str,
    body: str,
) -> None:
    """Envía después de responder la petición si hay BackgroundTasks."""
    if background_tasks is not None:
        background_tasks.add_task(send_email, to, subject, body)
    else:
        send_email(to, subject, body)


def send_verification_email(
    background_tasks: BackgroundTasks | None,
    user: "User",
    token: str,
) -> None:
    link = f"{settings.FRONTEND_URL}/verificar-correo?token={token}"

    _dispatch(
        background_tasks,
        user.email,
        "¡Bienvenido a TechZone! Confirma tu correo",
        f"Hola {user.full_name or user.username},\n\n"
        "Tu cuenta en TechZone fue creada. "
        "Para confirmar tu correo entra a este enlace:\n"
        f"{link}\n\n"
        f"El enlace vence en "
        f"{settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} horas.\n\n"
        "El equipo de TechZone",
    )


def send_password_reset_email(
    background_tasks: BackgroundTasks | None,
    user: "User",
    token: str,
) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    _dispatch(
        background_tasks,
        user.email,
        "Recupera tu contraseña de TechZone",
        f"Hola {user.full_name or user.username},\n\n"
        f"Para crear una nueva contraseña entra a este enlace:\n{link}\n\n"
        f"El enlace vence en "
        f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos. "
        "Si no lo solicitaste, ignora este correo.\n\n"
        "El equipo de TechZone",
    )


def send_advisory_completed_email(
    background_tasks: BackgroundTasks | None,
    advisory: "AdvisoryRequest",
) -> None:
    user = advisory.user

    _dispatch(
        background_tasks,
        user.email,
        "Tu asesoría personalizada está lista",
        f"Hola {user.full_name or user.username},\n\n"
        f"Un asesor respondió tu solicitud "
        f"\"{advisory.title}\". "
        f"Puedes ver la recomendación en "
        f"{settings.FRONTEND_URL}/asesorias/{advisory.id}\n\n"
        "El equipo de TechZone",
    )
