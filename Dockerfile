FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime

ARG RIPPLE_BUILD_REVISION="unknown"
ARG RIPPLE_BUILD_SOURCE="https://github.com/drakeg/twitclone"
ARG RIPPLE_BUILD_CREATED="unknown"

COPY . .

LABEL org.opencontainers.image.title="Ripple" \
      org.opencontainers.image.description="Ripple social networking application" \
      org.opencontainers.image.source="${RIPPLE_BUILD_SOURCE}" \
      org.opencontainers.image.revision="${RIPPLE_BUILD_REVISION}" \
      org.opencontainers.image.created="${RIPPLE_BUILD_CREATED}"

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "30", "application:application"]

FROM runtime AS development

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
