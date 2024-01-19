# === Linter's commands ===
ruff:
	poetry run ruff format

lint:
	poetry run xenon .
	poetry run ruff check . --fix

lint_docs:
	poetry run interrogate -v

mypy:
	poetry run mypy . $(args)

fmt: ruff lint

# === Test's commands ===
test:
	poetry run pytest --test-alembic --randomly-dont-reset-seed $(args)

test_cov:
	poetry run pytest --test-alembic --randomly-dont-reset-seed --cov $(args)

test_cov_html:
	poetry run pytest --test-alembic --randomly-dont-reset-seed --cov --cov-report=html

pre: fmt test_cov

# === Back-end commands ===
requirements:
	poetry export --without-hashes --only main -f requirements.txt -o requirements.txt

migrate:
	poetry run alembic upgrade head

run:
	poetry run gunicorn apps.__main__:app -c gunicorn.conf.py

update: migrate run
