#!/usr/bin/env bash
set -euo pipefail

# Параметры подключения к Postgres (для ожидания TCP)
: "${DB_HOST:?Set DB_HOST}"
: "${DB_PORT:=5432}"

# Необязательно: логируем URL, который возьмёт Alembic из env.py/alembic.ini
echo "DATABASE_URL=${DATABASE_URL:-<not set>}"

echo "⏳ Waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."
for i in {1..60}; do
  if nc -z "${DB_HOST}" "${DB_PORT}"; then
    echo "✅ Postgres is up"
    break
  fi
  sleep 1
done

# Прогоняем миграции (укажи правильный путь к INI, см. коммент ниже)
echo "🚀 Running Alembic migrations..."
python -m alembic upgrade head

# Стартуем приложение
echo "🌐 Starting app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
