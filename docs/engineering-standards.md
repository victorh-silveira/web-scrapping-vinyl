# Padrões de Engenharia e Qualidade

Todos os gates de qualidade são centralizados em `scripts/operations/clean_workspace.py` e executados de forma idêntica no `Makefile`, no `pre-commit` e no GitHub Actions.

## Gates Obrigatórios

| Estágio | Ferramentas / Regras |
|---|---|
| `lint` | `ruff check`, `ruff format --check`, `interrogate` (>=95% docstrings), `vulture` (código morto), `yamllint`, JSON lint |
| `validate` | `mypy --strict`, verificação AST de dependências entre camadas DDD, teto de **300 linhas** por arquivo `.py`, YAML/JSON validate |
| `security` | `bandit` (SAST), `pip-audit` (CVEs em dependências), `gitleaks` (segredos) |
| `test` | `coverage run --branch -m pytest` com exigência de **100% de cobertura** |
| `build` | `compileall` em `src/vinyl_scraper/` |
| `clean` | Limpeza de caches locais e artefatos temporários |
