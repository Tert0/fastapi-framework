FROM python:3.10.4-alpine

RUN apk add --no-cache build-base musl-dev gcc yaml-dev

WORKDIR /fastapi_framework

COPY coverage.sh .

COPY requirements.txt .

RUN pip install -r requirements.txt && pip install aiosqlite coverage httpx

COPY fastapi_framework/ ./fastapi_framework

COPY tests/ ./tests

RUN touch config.yaml

CMD chmod +x coverage.sh && ./coverage.sh
