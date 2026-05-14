# ========================
# Environment config
# ========================
SHELL := /bin/bash

APP_ENV_FILES :=

ifneq ($(wildcard .env),)
  APP_ENV_FILES += .env
endif

ifneq ($(wildcard .env.local),)
  APP_ENV_FILES += .env.local
endif

ifneq ($(wildcard .env.kc),)
  APP_ENV_FILES +=  .env.kc
endif

DOCKER_ENV_FILES := $(foreach f,$(APP_ENV_FILES),--env-file $f)

PY_RUN := make set-python-version;\
	PYTHONPATH=src uv run

REALM_RUN := make set-python-version;\
	PYTHONPATH=src uv run python src/pykeycloak_realm/realm.py

DC := docker compose
PYTHON_VER := $(shell [ -f .python-version ] && tr -d '\n' < .python-version || echo "")
CURRENT_VER := $(shell python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

define load_env
	set -a; \
	for f in $(env); do \
		[ -f "$$f" ] && . "$$f"; \
	done; \
	set +a
endef


# ========================
# PHONY Targets
# ========================
.PHONY: default help install clean run tests \
        docker-up docker-down docker-reset docker-ps docker-restart \
        pre-commit pre-commit-install pre-commit-update \
        script-% set-python-version

default: help

# ========================
# Aliases
# ========================
dup: docker-up  ## Alias: docker-up
dd: docker-down  ## Alias: docker-down
dr: docker-reset  ## Alias: docker-reset
dps: docker-ps  ## Alias: docker-ps
de-kc: docker-exec-keycloak  ## Alias: docker-exec-keycloak
dl-kc: docker-logs-keycloak  ## Alias: docker-logs-keycloak
dre: docker-restart ## Alias: docker-restart

otago: docker-kc-build-realm-otago ## Apply otago for KC

# ========================
# Help
# ========================
help:
	@echo ""
	@echo "📦 Project Makefile Commands:"
	@echo "---------------------------------------------"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_\/.%+-]+:.*## / { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ========================
# Project Setup
# ========================
install: ## Install dependencies and pre-commit hooks
	@make set-python-version
	@uv sync
	@uv run pre-commit install

clean: ## Remove .pyc files and pre-commit cache
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -exec rm -r {} +
	@uv run pre-commit clean

# ========================
# Run Realm Generator
# ========================

run-gen-realm: ## Run Realm Generator
	@$(load_env); $(REALM_RUN) rb

# ========================
# Formatting & Linting
# ========================
format: ## Format code using Black and Ruff
	@uv run pre-commit run black --all-files
	@uv run pre-commit run ruff --all-files

lint: ## Lint code using Ruff
	@uv run pre-commit run ruff --all-files

# ========================
# Pre-commit
# ========================
pre-commit: ## Run all pre-commit hooks
	@uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	@uv run pre-commit install

pre-commit-update: ## Update pre-commit hooks
	@uv run pre-commit autoupdate

# ========================
# Docker Compose Commands
# ========================
docker-up: ## Start containers
	$(DC) $(DOCKER_ENV_FILES) up -d --build

docker-down: ## Stop containers
	$(DC) $(DOCKER_ENV_FILES) down

docker-logs-%: ## Tail logs
	$(DC) $(DOCKER_ENV_FILES) logs -f $*

docker-reset: ## Remove containers and volumes
	$(DC) $(DOCKER_ENV_FILES) down -v --remove-orphans

docker-ps: ## List containers
	$(DC) $(DOCKER_ENV_FILES) ps

docker-restart: ## Restart Docker containers
	$(MAKE) docker-down
	$(MAKE) docker-up

docker-exec-%: ## Enter the Docker container for example: docker-exec-keycloak
	$(DC) $(DOCKER_ENV_FILES) exec -ti $* bash

#docker-kc-export-realm-%: ## Export realm data from keycloak container: docker-kc-export-realm-master
#	@python3 -c 'print("-" * 55)'
#	$(DC) $(DOCKER_ENV_FILES) exec -i keycloak /opt/keycloak/bin/kc.sh export --realm $* --file /tmp/export-$*.json
#	$(DC) $(DOCKER_ENV_FILES) cp keycloak:/tmp/export-$*.json ./data/realms/export/
#	@echo "Realm $* exported to ./data/realms/export/"
#	@python3 -c 'print("-" * 55)'

docker-kc-export-realm-%: ## Import template data to keycloak
	@python3 -c 'print("-" * 55)'
	@echo "===+> Validating JSON: ./data/realms/export/$*.realm.json"
	@python3 -m json.tool ./data/realms/export/$*.realm.json > /dev/null || { echo "❌ Invalid JSON in $*.realm.json"; exit 1; }
	@echo "===+>  ✅ JSON is valid. Importing realm '$*' into Keycloak..."
	@$(DC) $(DOCKER_ENV_FILES) exec -i keycloak /opt/keycloak/bin/realm_upload /opt/keycloak/data/export/$*.realm.json $*
	@python3 -c 'print("-" * 55)'

docker-kc-build-realm-%: ## Import generated data to keycloak
	@python3 -c 'print("\n")'
	@python3 -c 'print("-" * 55)'
	@echo "===+> Transform data from YAML to JSON: ./data/realms/templates/$*.realm.yml"
	@$(load_env); $(REALM_RUN) --from-realm $* --to-realm $*
	@echo "===+>  ✅ Realm transformation completed at ./data/realms/export/$*.realm.json ✅"
	@make docker-kc-export-realm-$*
	@python3 -c 'print("\n")'

# ========================
# Tests
# ========================
tests: ## Run all tests
	@$(load_env); $(PY_RUN) pytest tests -vv -s


release-bump: ## Sync pyproject version from GITHUB_REF_NAME (vX.Y.Z)
	@python3 bin/sync_version_from_tag.py

release-bump-tag: ## Sync pyproject version from TAG=vX.Y.Z
	@if [ -z "$(TAG)" ]; then \
		echo "TAG is required. Example: make release-bump-tag TAG=v0.7.4"; \
		exit 1; \
	fi
	@python3 bin/sync_version_from_tag.py --tag "$(TAG)"


# =========
# Helpers
# ==========

set-python-version:
	@if [ "$(CURRENT_VER)" != "$(PYTHON_VER)" ]; then \
	  	uv python pin $(PYTHON_VER); \
	 fi
