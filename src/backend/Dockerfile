# ---------- build ----------
FROM python:3.11-slim-bullseye AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY ../../requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev build-essential && \
    pip install --no-cache-dir pip wheel && \
    pip wheel --no-cache-dir --wheel-dir /opt/wheels -r requirements.txt && \
    apt-get purge -y gcc build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# ---------- final ----------
FROM python:3.11-slim-bullseye AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# для ожидания TCP-порта БД
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Установка wheels без компиляции
COPY --from=build /opt/wheels /opt/wheels
RUN pip install --no-cache-dir /opt/wheels/* && rm -rf /opt/wheels

# Копируем исходники приложения
COPY src/backend ./

# Копируем entrypoint
COPY src/backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE ${WEBHOOK_PORT}

# ВАЖНО: если alembic.ini не в adapters/db/migrations/alembic.ini — поменяй путь в entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
