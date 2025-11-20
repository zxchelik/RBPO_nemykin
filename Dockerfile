# syntax=docker/dockerfile:1

ARG LIBEXPAT_VERSION=2.5.0-1+deb12u1

FROM python:3.11.9-slim-bookworm AS builder
ARG LIBEXPAT_VERSION
ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /src
# hadolint ignore=DL3008,DL3018
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libffi-dev libssl-dev libexpat1=${LIBEXPAT_VERSION} \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==24.2 wheel==0.44.0 \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11.9-slim-bookworm AS runtime
ARG LIBEXPAT_VERSION
LABEL org.opencontainers.image.source="https://github.com/ZXCheliK/course-project"
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app
WORKDIR /app
# hadolint ignore=DL3008,DL3018
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl netcat-openbsd libexpat1=${LIBEXPAT_VERSION} \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /tmp/wheels
RUN pip install --no-cache-dir --no-deps /tmp/wheels/* \
    && rm -rf /tmp/wheels
COPY src/backend/ ./
RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app \
    && chmod +x /app/entrypoint.sh
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1
ENTRYPOINT ["/app/entrypoint.sh"]
