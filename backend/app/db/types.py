from enum import Enum as PyEnum

from sqlalchemy import Enum


def enum_column(enum_cls: type[PyEnum]) -> Enum:
    """Guarda el valor del enum como texto en lugar de crear un ENUM nativo de PostgreSQL."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=30,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )
