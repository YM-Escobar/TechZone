from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping evita errores con conexiones que Neon cierra por inactividad
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass
