# fastapi_quickstart (In development, WIP)!!!
Initial FastAPI project with SQLAlchemy (asyncpg), Alembic, Pydantic v2, Pytest, Poetry, Gunicorn, Docker, docker-compose, ruff, black, isort, flake8, coverage, factory-boy, pytest-alembic, pydantic-factories.

## Dependencies:
- [uv](https://docs.astral.sh/uv/) (For Python, package and dependencies management)
- [Docker & docker-compose](https://www.docker.com/products/docker-desktop/) (For containerization of app)
- [Taskfile](https://taskfile.dev/installation/) (Commands runner)


## Setup
#### Create `.env` file (based on example.env)
```commandline
cp example.env .env
```

#### Download python with uv
```commandline
uv python install 3.12
```

#### Pin python (optional)
```commandline
uv python pin 3.12
```

#### Activate environment
```commandline
uv venv
```

#### Install packages (for local development)
```commandline
uv sync --all-groups
```

### Run all containers (PostgreSQL, PGAdmin, Redis, RedisInsights)
```commandline
docker-compose up -d
```

### Run Back-end
#### docker-compose (local container)
It also possible to uncomment backend service inside docker-compose.yml and run
through the docker compose.
> **_Note:_** Set `POSTGRES_HOST` to `postgres` (`POSTGRES_HOST=postgres`) inside .env file

#### Uvicorn (local)
```commandline
task run:uvicorn
```

#### With Gunicorn & UvicornWorker (like a prod)
```commandline
task run
```

---

## Tech stack

### Package & Dependencies Management
- uv (with pyproject.toml)

### Infrastructure
- Docker
- docker-compose
  - db (PostgreSQL latest)
  - pgadmin (PGAdmin — GUI for PostgreSQL simplifies query creation, profiling and management, debugging)
  - redis (Redis latest)
  - redis_insights (Redis Insights — GUI for Redis)
  - backend (Commented — possible to run Back-end via docker-compose)

### Tests
- pytest (with pytest-asyncio)
- pytest-cov (for run tests with coverage)
- pytest-mock (to use `mocker` fixture)
- pytest-randomly (to random sort tests in runtime)
- pytest-clarity (for better tests fails descriptions)
- Faker (to generate random data)
- pytest-alembic (to run tests on migrations)
- factory-boy (to generate model factories in db)

### Debugging
- iPython (enhanced console for Python)

### Linters & Formatters
- ruff (Rust based linter & formatter)
- xenon (code linter, complexity linter)
- mypy (code linter, type annotations linter)

### Frameworks
- FastAPI (Starlette) (ASGI web framework)
- typer (CLI creation framework)

### DB drivers & tools
- SQLAlchemy (ORM, Core, db schema declaration)
- alembic (DB migrations tool)
- psycopg2-binary (sync driver for working with PostgreSQL)
- asyncpg (async driver for working with PostgreSQL)
- aioredis (async driver for working with Redis)

### Extra libraries
- httpx (async client library)
- orjson (fast JSON serialization/deserialization)
- pydantic v2 (JSON & data validation tool)
- uvicorn (ASGI web server implementation)
- gunicorn (process management tool)
- bcrypt (hashing library, passwords hashing)
- PyJWT (library for working with JWT tokens)
