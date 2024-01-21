FROM python:3.11

ENV PYTHONPATH=/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

RUN pip install --upgrade pip

RUN pip install poetry

WORKDIR /backend

COPY Taskfile.yaml Makefile pyproject.toml /backend/

RUN task req

RUN pip install --no-cache-dir --upgrade -r /backend/requirements.txt

COPY . /backend

EXPOSE 8000

CMD ["task", "run"]
