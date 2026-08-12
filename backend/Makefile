.PHONY: install migrate seed run test

install:
	pip install -r requirements.txt --break-system-packages

migrate:
	alembic upgrade head

seed:
	python seed.py

run:
	uvicorn app.main:app --reload --port 8000
