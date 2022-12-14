# fastapi_quickstart (In development, WIP)!!!
Initial FastAPI project with SQLAlchemy (asyncpg), Alembic, Pydantic, Pytest, Poetry, Gunicorn, Docker, docker-compose, black, isort, flake8, coverage, factory-boy, pytest-alembic, pydantic-factories. 

## Tech stack

### Package & Dependencies Management
- poetry (with pyproject.toml)

### Infrastructure
- Docker
- docker-compose
  - db (PostgreSQL latest)
  - pgadmin (PGAdmin - GUI for PostgreSQL simplifies query creation, profiling and management, debugging)
  - redis (Redis latest)
  - redis_insights (Redis Insights - GUI for Redis)
  - backend (Commented - possibility to run Back-end via docker-compose)

### Tests
- pytest (with pytest-asyncio)
- pytest-cov (for run tests with coverage)
- pytest-mock (to use `mocker` fixture)
- pytest-randomly (to random sort tests in runtime)
- pytest-clarity (for better tests fails descriptions)
- Faker (to generate random data)
- pytest-alembic (to run tests on migrations)
- pydantic-factories (to generate schema factories)
- factory-boy (to generate model factories in db)

### Debugging
- iPython (enhanced Python's console)

### Linters & Formatters
- black (code formatter, PEP8)
- isort (code formatter, sort imports)
- flake8 (code linter)
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
- pydantic (JSON & data validation tool)
- uvicorn (ASGI web server implementation)
- gunicorn (process management tool)
- bcrypt (hashing library, passwords hashing)
- PyJWT (library for working with JWT tokens)
