.PHONY: up down logs migrate test shell

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f app

migrate:
	docker compose exec app alembic upgrade head

test:
	docker compose exec app pytest

shell:
	docker compose exec app bash
