FROM node:22-alpine AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash \
       build-essential \
       libpq-dev \
       libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN addgroup --system appgroup && adduser --system --no-create-home appuser --ingroup appgroup
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend /frontend/dist /app/frontend/dist

RUN mkdir -p /app/media && chmod -R +w /app/media
RUN chmod +x /app/docker/web/entrypoint.sh
RUN chmod +x /app/docker/celery/entrypoint.sh
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
