import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import BadRequestError

UPLOAD_URL_PREFIX = "/uploads"

# Firma de bytes iniciales de cada formato permitido, para no confiar en la extensión
IMAGE_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
]


def upload_root() -> Path:
    return Path(settings.UPLOAD_DIR).resolve()


def max_upload_bytes() -> int:
    return settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _detect_image_extension(content: bytes) -> str | None:
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    for signature, extension in IMAGE_SIGNATURES:
        if content.startswith(signature):
            return extension
    return None


def save_image(content: bytes, folder: str) -> str:
    """Guarda la imagen y devuelve la URL relativa con la que se sirve (p. ej. /uploads/avatars/x.png)."""
    if not content:
        raise BadRequestError("El archivo está vacío")
    if len(content) > max_upload_bytes():
        raise BadRequestError(f"La imagen supera el máximo de {settings.MAX_UPLOAD_SIZE_MB} MB")
    extension = _detect_image_extension(content)
    if extension is None:
        raise BadRequestError("Formato no permitido. Usa JPG, PNG, WEBP o GIF")

    directory = upload_root() / folder
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (directory / filename).write_bytes(content)
    return f"{UPLOAD_URL_PREFIX}/{folder}/{filename}"


def delete_image(url: str | None) -> None:
    """Borra un archivo subido antes; ignora URLs externas o archivos que ya no existen."""
    if not url or not url.startswith(f"{UPLOAD_URL_PREFIX}/"):
        return
    root = upload_root()
    path = (root / url.removeprefix(f"{UPLOAD_URL_PREFIX}/")).resolve()
    if path.is_relative_to(root) and path.is_file():
        path.unlink()
