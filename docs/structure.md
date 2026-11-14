# Inventário Estrutural

```text
web-scrapping-vinyl/
├── .agents/                    # Harness canônico de agentes generalistas
│   ├── agents/                 # Personas (architect, qa-tester, devops-secops, release-engineer)
│   ├── rules/                  # Regras universais (.mdc)
│   ├── skills/                 # Habilidades especializadas (SKILL.md)
│   └── mcp.json                # Manifesto MCP
├── .github/
│   ├── actions/ci/             # Composite actions (setup-python, workflows, release, pipeline-summary)
│   └── workflows/ci.yml        # Pipeline CI/CD bidirecional com pre-commit
├── data/
│   └── vinyls.example.json     # Catálogo JSON de exemplo
├── docs/                       # Documentação técnica e CHANGELOG
├── linters/                    # Commitlint, Semantic Release, Pre-commit e git-hooks
├── scripts/operations/         # Clean Workspace (SSOT de lint, validate, security, test, build, clean)
├── src/vinyl_scraper/
│   ├── domain/                 # Núcleo puro DDD
│   ├── application/            # Casos de uso e DTOs
│   ├── infrastructure/         # Scrapers, SQLite, JSON I/O, External
│   └── presentation/           # CLI (Typer + Rich)
├── tests/                      # Suíte TDD (unit + integration + fixtures)
├── AGENTS.md                   # Manifesto SSOT para agentes de IA
├── Makefile                    # Orquestração local
├── pyproject.toml              # Dependências e configuração de ferramentas
└── README.md                   # Visão geral e guia de uso
```
