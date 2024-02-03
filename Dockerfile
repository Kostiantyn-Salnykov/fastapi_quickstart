FROM python:3.12

ENV PYTHONPATH=/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

RUN pip install --upgrade pip

RUN pip install poetry

WORKDIR /backend

COPY Taskfile.yaml pyproject.toml poetry.lock /backend/

RUN poetry config virtualenvs.create false && poetry install

COPY . /backend

EXPOSE 8000

CMD ["task", "run"]
