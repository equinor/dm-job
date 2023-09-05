FROM python:3.11-slim as base
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code/src
WORKDIR /code
CMD ["/code/src/init.sh", "api"]
EXPOSE 5000

RUN apt-get update -y && apt-get full-upgrade -y && apt-get install -y curl

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

FROM base as development
RUN poetry install
WORKDIR /code/src
COPY src /code/src/
COPY app /code/app/
COPY .flake8 .bandit ./


FROM base as prod
RUN poetry install --no-dev
WORKDIR /code/src
COPY src /code/src/
COPY app /code/app/
USER 1000
