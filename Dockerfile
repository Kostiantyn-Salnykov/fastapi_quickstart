FROM python:3.12

RUN useradd -ms /bin/sh user

ENV PYTHONPATH=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.0

ENV PATH="$PATH:$POETRY_HOME/bin"

RUN apt-get update && apt-get install -y --no-install-recommends curl

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /backend

COPY Taskfile.yaml pyproject.toml poetry.lock /backend/

RUN poetry config virtualenvs.create false && poetry install

USER user

COPY --chown=user:user . /backend

EXPOSE 8000

CMD ["task", "run"]
