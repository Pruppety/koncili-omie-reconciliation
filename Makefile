.PHONY: install fake-data run test lint docker-build docker-run airflow-up

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

fake-data:
	python scripts/generate_fake_data.py

run:
	reconciler

test:
	pytest --cov=reconciler --cov-report=term-missing

lint:
	ruff check src tests

docker-build:
	docker build -t reconciler .

docker-run:
	docker run -v "$(CURDIR)/data:/app/data" reconciler

airflow-up:
	docker compose up
