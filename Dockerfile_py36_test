# Dockerfile to test old-style client usage based on httpx for old Python 3.6

FROM python:3.6-slim-buster

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools poetry

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
RUN poetry install

COPY tests /app/tests
COPY pyuploadcare /app/pyuploadcare

CMD ["poetry", "run", "pytest", "-v", "tests/"]
