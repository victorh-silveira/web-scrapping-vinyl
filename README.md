# Amazon BR Vinyl Smart Scraper

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](.python-version)
[![Architecture](https://img.shields.io/badge/Architecture-DDD%20%7C%20Clean%20%7C%20SOLID-0A66C2)](docs/arquitetura.md)
[![Types](https://img.shields.io/badge/mypy-strict-2A6DB0?logo=python&logoColor=white)](pyproject.toml)
[![Lint](https://img.shields.io/badge/Ruff-lint%20%7C%20format-D7FF64?logo=ruff&logoColor=black)](pyproject.toml)
[![Coverage](https://img.shields.io/badge/coverage-100%25%20branch-0F9D58)](docs/engineering-standards.md)
[![Tests](https://img.shields.io/badge/pytest-TDD%20unit%20%7C%20integration-0F9D58?logo=pytest&logoColor=white)](tests)
[![Security](https://img.shields.io/badge/security-bandit%20%7C%20pip--audit%20%7C%20gitleaks-C0392B)](docs/engineering-standards.md)
[![Pre-commit](https://img.shields.io/badge/pre--commit-gates%20ativos-FAB040?logo=pre-commit&logoColor=white)](linters/pre-commit-config.yaml)
[![Commits](https://img.shields.io/badge/commits-Conventional%20Commits-FE5196?logo=conventionalcommits&logoColor=white)](linters/commitlint.config.mjs)
[![Release](https://img.shields.io/badge/release-semantic--release-494949?logo=semanticrelease&logoColor=white)](linters/releaserc.json)
[![CI](https://github.com/victorh-silveira/web-scrapping-vinyl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/victorh-silveira/web-scrapping-vinyl/actions/workflows/ci.yml)

WebScraper inteligente para discos de vinil na **Amazon BR (`amazon.com.br`)**, desenvolvido em **Python 3.13** com **DDD**, **TDD**, **SOLID** e **Clean Architecture**.

---

## Funcionalidades

- **Leitura via JSON**: Carrega lista de discos desejada, preço-alvo e edições preferidas (`data/vinyls.example.json`).
- **Descoberta de Todas as Versões**: Identifica e classifica múltiplas edições do mesmo álbum (ex.: *Thriller* -> *25th Anniversary*, *40th Anniversary*, *Picture Disc*, *180g*, *2LP*, *Importado*, *Remastered*), filtrando não-vinis (CD, MP3, livros, camisetas).
- **Histórico Híbrido de Preços**: Acumula snapshots temporais em SQLite local + preço "De/Por" da Amazon, com `ExternalPriceHistoryPort` pronta para plugar Keepa API.
- **Estatísticas & Black Friday**: Calcula **média**, **mediana**, **mínimo/máximo histórico**, comparativo **Pré-Black Friday vs. Black Friday**, detecção de **falso desconto** ("metade do dobro") e **score de custo-benefício** (`0..100`).
- **Exportação JSON + CLI Rich**: Gera relatório JSON ranqueado e exibe tabelas formatadas no terminal.

---

## Arquitetura & Documentação

- [Arquitetura Técnica (DDD + Clean Architecture)](docs/arquitetura.md)
- [Inventário Estrutural](docs/structure.md)
- [Padrões de Engenharia e Quality Gates](docs/engineering-standards.md)
- [CI/CD Bidirecional & Semantic Release](docs/engineering-ci-release.md)
- [Harness de Agentes Generalistas](AGENTS.md)
- [Matriz de Cobertura de Agentes](docs/agent-coverage.md)

---

## Operação via Makefile & Clean Workspace

```bash
# Menu interativo
make help

# Setup completo (dependências + Playwright + hooks pre-commit)
make app-setup

# Executar busca e análise na Amazon BR
make app-run ARGS="--input data/vinyls.example.json --output output/report.json"

# Quality Gates (idênticos ao Pre-commit e ao CI/CD)
make app-lint
make app-validate
make app-security
make app-test
make app-build
make app-clean
```
