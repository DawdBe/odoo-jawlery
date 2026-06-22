.DEFAULT_GOAL := help

PROJECT_NAME := $(shell basename $(CURDIR))
DB_NAME ?= postgres

help:
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║    $(PROJECT_NAME) - Odoo Project                       ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  BUILD & RUN"
	@echo "  make build        Build the custom Odoo Docker image"
	@echo "  make up           Start all services (detached)"
	@echo "  make down         Stop all services"
	@echo "  make restart      Restart all services"
	@echo "  make logs         Tail logs from the Odoo container"
	@echo "  make ps           Show running containers"
	@echo ""
	@echo "  MODULE MANAGEMENT"
	@echo "  make module name=my_module         Scaffold a new addon module"
	@echo "  make upgrade module=my_module      Upgrade a specific module"
	@echo "  make install module=my_module      Install a specific module"
	@echo "  make list-modules                  List installed custom modules"
	@echo ""
	@echo "  DATABASE"
	@echo "  make db-drop       Drop the Odoo database"
	@echo "  make db-shell      Open psql shell to the database"
	@echo "  make backup        Backup the database to ./backups/"
	@echo ""
	@echo "  DEVELOPMENT"
	@echo "  make shell         Open an odoo shell in the running container"
	@echo "  make bash          Open a bash shell in the Odoo container"
	@echo "  make update-all    Update all modules"
	@echo ""
	@echo "  TESTING"
	@echo "  make test module=my_module      Run tests for a module"
	@echo "  make test-all                   Run all tests"
	@echo ""

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f odoo

ps:
	docker compose ps

module:
	@if [ -z "$(name)" ]; then \
		echo "Usage: make module name=module_name"; \
		exit 1; \
	fi
	@scripts/create-module.sh $(name)

upgrade:
	@if [ -z "$(module)" ]; then \
		echo "Usage: make upgrade module=module_name"; \
		exit 1; \
	fi
	@docker compose exec odoo odoo -d $(DB_NAME) -u $(module) --stop-after-init

install:
	@if [ -z "$(module)" ]; then \
		echo "Usage: make install module=module_name"; \
		exit 1; \
	fi
	@docker compose exec odoo odoo -d $(DB_NAME) -i $(module) --stop-after-init

list-modules:
	@docker compose exec odoo odoo -d $(DB_NAME) --stop-after-init 2>&1 | grep -oP "'\K[^']+(?=': module)" || true

db-drop:
	@echo "Dropping database $(DB_NAME)..."
	@docker compose exec db dropdb -U odoo $(DB_NAME)
	@docker compose exec db createdb -U odoo $(DB_NAME)
	@echo "Database $(DB_NAME) recreated."

db-shell:
	docker compose exec db psql -U odoo -d $(DB_NAME)

backup:
	@mkdir -p backups
	docker compose exec db pg_dump -U odoo $(DB_NAME) > backups/$(DB_NAME)_$(shell date +%Y%m%d_%H%M%S).sql

shell:
	docker compose exec odoo odoo shell -d $(DB_NAME)

bash:
	docker compose exec odoo bash

update-all:
	docker compose exec odoo odoo -d $(DB_NAME) -u all --stop-after-init

test:
	@if [ -z "$(module)" ]; then \
		echo "Usage: make test module=module_name"; \
		exit 1; \
	fi
	docker compose exec odoo odoo -d $(DB_NAME) -u $(module) --test-tags $(module) --stop-after-init 2>&1

test-all:
	docker compose exec odoo odoo -d $(DB_NAME) --test-tags all --stop-after-init 2>&1

.PHONY: help build up down restart logs ps module upgrade install list-modules db-drop db-shell backup shell bash update-all test test-all
