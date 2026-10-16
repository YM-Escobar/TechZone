from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TechZone API"
    API_PREFIX: str = "/api"

    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48

    # Si es True, los usuarios sin correo verificado no pueden publicar, comentar ni pedir asesorías
    REQUIRE_EMAIL_VERIFICATION: bool = False

    # Archivos subidos (avatares e imágenes de productos)
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:4321"
    CORS_ORIGINS: list[str] = ["http://localhost:4321"]

    # Administrador inicial: se crea al arrancar si no existe
    FIRST_ADMIN_EMAIL: str | None = None
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str | None = None

    # SMTP: si no se configura SMTP_HOST, los correos solo se escriben en el log
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "TechZone <no-reply@techzone.com>"
    SMTP_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Neon entrega URLs "postgresql://", pero el driver instalado es psycopg (v3)
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


settings = Settings()
