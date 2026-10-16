import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.Models.user import User, UserRole
from app.Repository.user_repository import UserRepository

logger = logging.getLogger("techzone")

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def run_migrations() -> None:
    config = Config(str(ALEMBIC_INI))
    # Evita que Alembic reemplace la configuración de logs de la app
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")


def create_first_admin() -> None:
    if not (settings.FIRST_ADMIN_EMAIL and settings.FIRST_ADMIN_PASSWORD):
        return

    with SessionLocal() as db:
        users = UserRepository(db)
        if users.get_by_email(settings.FIRST_ADMIN_EMAIL) is None:
            users.add(User(
                email=settings.FIRST_ADMIN_EMAIL.lower(),
                username=settings.FIRST_ADMIN_USERNAME,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_verified=True,
            ))
            logger.info("Administrador inicial creado: %s", settings.FIRST_ADMIN_EMAIL)


def init_db() -> None:
    run_migrations()
    create_first_admin()
