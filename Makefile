# === Linter's commands ===
black:
	poetry run black . $(args)

lint:
	poetry run flake8 $(args)
	poetry run xenon .

lint_plus:
	poetry run ruff check .

isort:
	poetry run isort . $(args)

mypy:
	poetry run mypy . $(args)

fmt: black isort lint

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
	poetry run gunicorn apps.main:app -c gunicorn.conf.py

update: migrate run
