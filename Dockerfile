FROM python:3.10.12-alpine

RUN apk add --no-cache build-base musl-dev gcc yaml-dev

WORKDIR /fastapi_framework

COPY coverage.sh .

#COPY requirements.txt .
COPY README.md .
COPY pyproject.toml .

COPY fastapi_framework/ ./fastapi_framework

#RUN pip install -r requirements.txt && pip install aiosqlite coverage httpx
RUN pip install -e .[test]

COPY tests/ ./tests

RUN touch config.yaml

CMD chmod +x coverage.sh && ./coverage.sh
