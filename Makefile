# ==============================================================================
#              AMAZON BR VINYL SCRAPER - CORE MATRIX MAKEFILE
# ==============================================================================

SHELL := /bin/bash
PRE_COMMIT_CONFIG=linters/pre-commit-config.yaml
ARGS ?= --input data/vinyls.json --output output/report.json

PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; elif [ -x .venv/Scripts/python.exe ]; then echo .venv/Scripts/python.exe; elif command -v python3 >/dev/null 2>&1; then command -v python3; else echo python; fi)

GREEN  := \033[1;32m
YELLOW := \033[1;33m
BLUE   := \033[1;34m
CYAN   := \033[1;36m
RESET  := \033[0m

.DEFAULT_GOAL := help

.PHONY: help app-install app-run app-lint app-validate app-security app-test app-build app-clean \
	app-pre-commit app-pre-commit-run app-setup \
	install run lint validate security test build clean pre-commit

help:
	@echo -e "$(BLUE)========================================================================$(RESET)"
	@echo -e "$(GREEN)             AMAZON BR VINYL SCRAPER - MENU DE AJUDA                   $(RESET)"
	@echo -e "$(BLUE)========================================================================$(RESET)"
	@echo -e "Uso: $(CYAN)make <comando>$(RESET)"
	@echo -e ""
	@echo -e "$(YELLOW)Python:$(RESET) $(PYTHON)"
	@echo -e ""
	@echo -e "$(YELLOW)App:$(RESET)"
	@echo -e "  $(GREEN)app-install$(RESET)          - Instala dependencias (pyproject.toml + dev + Playwright)"
	@echo -e "  $(GREEN)app-run$(RESET)              - Executa busca e analise (ARGS='--input data/vinyls.example.json')"
	@echo -e "  $(GREEN)app-setup$(RESET)            - Install + hook commit-msg (crash-first)"
	@echo -e "  $(GREEN)app-clean$(RESET)            - Limpa caches e artefatos locais"
	@echo -e ""
	@echo -e "$(YELLOW)Qualidade (SSOT Clean Workspace <-> Pre-commit <-> CI/CD):$(RESET)"
	@echo -e "  $(GREEN)app-lint$(RESET)             - Ruff check/format + Interrogate + Vulture + YAML/JSON"
	@echo -e "  $(GREEN)app-validate$(RESET)         - Mypy strict + AST camadas DDD + teto 300 linhas"
	@echo -e "  $(GREEN)app-security$(RESET)         - Bandit + pip-audit + Gitleaks"
	@echo -e "  $(GREEN)app-test$(RESET)             - Pytest + cobertura branch 100%"
	@echo -e "  $(GREEN)app-build$(RESET)            - Compileall de todo src/"
	@echo -e "  $(GREEN)app-pre-commit$(RESET)       - Instala hook commit-msg"
	@echo -e "  $(GREEN)app-pre-commit-run$(RESET)   - Roda hooks bidirecionais no stage commit-msg"
	@echo -e "$(BLUE)========================================================================$(RESET)"

app-install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m playwright install chromium

app-run:
	$(PYTHON) -m vinyl_scraper.presentation.cli run $(ARGS)

app-lint:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage lint

app-validate:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage validate

app-security:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage security

app-test:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage test --coverage-fail-under 100

app-build:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage build

app-clean:
	$(PYTHON) scripts/operations/clean_workspace.py --area python --stage clean

app-pre-commit:
	chmod +x linters/git-hooks/bin/python linters/git-hooks/bin/resolve_venv_python.sh
	$(PYTHON) -m pre_commit install --hook-type commit-msg --config $(PRE_COMMIT_CONFIG)

app-pre-commit-run:
	chmod +x linters/git-hooks/bin/python linters/git-hooks/bin/resolve_venv_python.sh
	@printf '%s\n' 'chore(repo): validacao local dos hooks' > .git/VINYL_COMMITLINT_MSG
	$(PYTHON) -m pre_commit run --all-files -c $(PRE_COMMIT_CONFIG) \
		--hook-stage commit-msg --commit-msg-filename .git/VINYL_COMMITLINT_MSG

app-setup: app-install app-pre-commit

install: app-install
run: app-run
lint: app-lint
validate: app-validate
security: app-security
test: app-test
build: app-build
clean: app-clean
pre-commit: app-pre-commit
