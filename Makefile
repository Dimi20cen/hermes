.PHONY: install dev test

install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --port 8010

test:
	pytest -q

