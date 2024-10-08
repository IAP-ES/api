FROM python:3.13-slim as requirements-stage

ENV PYTHONUNBUFFERED 1

WORKDIR /api

RUN apt-get update

RUN pip install --upgrade pip 
RUN pip install --no-cache-dir --upgrade poetry

COPY poetry.lock pyproject.toml ./

COPY . .

RUN poetry install

EXPOSE 8000

CMD poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload