FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --create-home app

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

USER app

EXPOSE 10000

CMD ["/bin/sh", "-c", "python -m alembic upgrade head && exec python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
