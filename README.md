# Task Tracker

Личный таск-менеджер с приоритетами, дедлайнами и фильтрацией.
MVP включает CRUD задач, авторизацию пользователей и работу только с собственными задачами.

## Содержание
- [Содержание](#содержание)
- [Требования окружения](#требования-окружения)
- [Установка и запуск](#установка-и-запуск)
- [Конфигурация](#конфигурация)
- [Тесты и качество](#тесты-и-качество)
- [Контейнеризация](#контейнеризация)
- [API (если применимо)](#api-если-применимо)
- [Архитектура](#архитектура)
- [Безопасность](#безопасность)
- [Отладка CI](#отладка-ci)
- [Лицензия](#лицензия)

---

## Требования окружения
- Python >= 3.11
- Git
- Docker Engine + Compose V2 (для контейнерного запуска)
- make, hadolint, Trivy — опционально, для локальных проверок

---

## Установка и запуск
### Локально
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
````

Запуск приложения:

```bash
uvicorn app.main:app --reload
```

### В Docker

1. Скопируйте переменные окружения и задайте реальные значения:
   ```bash
   cp .env.example .env
   ````
2. Соберите образ и поднимите стек (FastAPI + PostgreSQL):
   ```bash
   docker compose up --build
   ```
   или через `make`:
   ```bash
   make docker-build
   make compose-up
   ```
3. После старта убедитесь, что контейнеры **healthy**:
   ```bash
   docker compose ps
   ```
4. Проверка порта API и пользователя процесса:
   ```bash
   curl http://localhost:8000/health
   docker compose exec backend id
   ```
5. Остановка стека: `make compose-down` или `docker compose down --remove-orphans`.

---

## Конфигурация

* Используйте `.env` (см. `.env.example`) и **не** коммитьте реальные значения.
* Основные переменные:
  * `DB_HOST` — адрес PostgreSQL (по умолчанию `postgres` в Compose);
  * `DB_USER` / `DB_PASSWORD` — учётные данные БД;
  * `SECRET_KEY` — ключ для JWT.
* `src/backend/config.yaml` подтягивает значения из `.env`, так что можно управлять конфигом без правок кода.
* Для production рекомендуется передавать переменные через секреты CI/CD и/или Docker secrets.

---

## Тесты и качество

```bash
ruff check --fix . && black . && isort .
mypy src
bandit -c bandit.yaml
pytest --cov
pre-commit run --all-files
```

Дополнительно для контейнера:

```bash
make hadolint   # линтер Dockerfile
make trivy      # SCA/вулны образа (нужен докер-демон)
```

Покрытие тестами планируется для CRUD задач, авторизации (owner-only) и фильтрации по статусу/дедлайну.

## Контейнеризация

- `Dockerfile` — многостадийный, базируется на `python:3.11.9-slim-bookworm`, устанавливает зависимости из wheel'ов и запускает FastAPI под пользователем `app` (UID 1001).
- `HEALTHCHECK` в образе и `docker-compose.yaml` пингуют `/health`, чтобы контейнер гарантированно становился `healthy`.
- Файлы загрузок пишутся в примонтированный volume `uploads-data`, остальная файловая система монтируется только для чтения, `tmpfs` используется для `/tmp`.
- Compose включает PostgreSQL 16.4 (alpine) с собственным healthcheck’ом, запретом лишних capabilities и опцией `no-new-privileges` для API.
- Все зависимости и базовые образы зафиксированы по версиям, что позволяет воспроизводимо собирать prod-образ.

**Проверки безопасности контейнера**

- `hadolint` запускается в CI и локально через `make hadolint`.
- `Trivy` собирает отчёт (артефакт `trivy-report`) и падает при нахождении критичных уязвимостей; High остаются заметными в отчёте.
- CI дополнительно собирает hardened-образ, чтобы гарантировать воспроизводимость.

---

## API

* Базовый URL: `/api/v1`
* Примеры эндпоинтов:

  * `POST /auth/login` — вход пользователя
  * `POST /tasks` — создать задачу
  * `GET /tasks` — получить список задач
  * `GET /tasks/{id}` — получить задачу по ID
  * `PUT /tasks/{id}` — обновить задачу
  * `DELETE /tasks/{id}` — удалить задачу

Формат ошибок:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "...",
  "details": {...}
}
```

---

## Архитектура

* `app/main.py` — точка входа FastAPI
* `app/api/` — маршруты (auth, tasks)
* `app/models/` — SQLAlchemy модели
* `app/schemas/` — Pydantic схемы
* `app/services/` — бизнес-логика
* `app/core/` — конфиги, зависимости, настройки БД
* `app/tests/` — тесты Pytest
* `app/logs/` — логи приложения

**Доменные правила:**

* Пользователь работает только со своими задачами (**owner-only**)
* Статусы задач: `todo`, `in_progress`, `done`
* Приоритет: `low`, `medium`, `high`
* Подготовка к будущим фичам: Канбан, повторяющиеся задачи, уведомления

---

## Безопасность

* Валидация ввода и статусов задач
* Авторизация через JWT, хранение паролей в захэшированном виде
* Доступ только к своим задачам
* Секреты и конфигурации вне репозитория
* Логи не содержат чувствительных данных
* Контейнер запускается под непривилегированным пользователем, с `cap_drop: ["ALL"]`, `no-new-privileges` и healthcheck’ами

---

## Отладка CI

* Смотрите вкладку Actions → последний Failed шаг (линтеры, тесты, hadolint или Trivy)
* Типовые исправления:

```bash
ruff --fix .
black .
isort .
pytest -q
make hadolint
docker build --target runtime .
```

---

## Лицензия

MIT
