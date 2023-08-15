FROM python:3.10-slim as base
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/code/src
WORKDIR /code
ENTRYPOINT ["/code/src/init.sh"]
CMD ["api"]
EXPOSE 5000

RUN apt-get update -y && apt-get full-upgrade -y && apt-get install -y curl && apt install build-essential -y
RUN apt-get install azure-cli -y

ENV PATH="/code/.venv/bin:$PATH"

RUN useradd --system --uid 1000 nonrootuser

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./

FROM base as development
RUN poetry install
WORKDIR /code/src
COPY src /code/src/
COPY app /code/app/
COPY .flake8 .bandit ./
RUN chown -R nonrootuser /home
USER nonrootuser
CMD ["api"]


FROM base as prod
RUN poetry install --no-dev
WORKDIR /code/src
COPY src /code/src/
COPY app /code/app/
RUN chown -R nonrootuser /home
USER nonrootuser
CMD ["api"]
