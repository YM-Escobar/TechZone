FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios; uploads/ es donde se guardan avatares e imágenes
RUN useradd --create-home appuser && mkdir -p uploads && chown -R appuser /app/uploads
USER appuser

EXPOSE 8000

# Las migraciones de Alembic se aplican automáticamente al arrancar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
