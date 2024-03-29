FROM python:3.10-slim as base
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code/src
WORKDIR /code
ENTRYPOINT ["/code/src/init.sh"]
CMD ["/code/src/init.sh", "api"]
EXPOSE 5000

RUN apt-get update -y && apt-get full-upgrade -y && apt-get install -y curl gettext

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
RUN chown -R 1000:1000 /code/app/
USER 0

FROM base as prod
RUN poetry install --no-dev
WORKDIR /code/src
COPY src /code/src/
COPY app /code/app/
RUN chown -R 1000:1000 /code/app/
USER 1000
