# AGENTS.md — Manifesto do Harness de IA do Amazon BR Vinyl Scraper

Ponto de entrada canônico e Single Source of Truth (SSOT) para agentes de inteligência artificial e desenvolvedores operando neste repositório.

---

## 1. Idioma e Ambiente Operacional

- **Idioma Obrigatório**: Respostas, documentações técnicas, docstrings Python e mensagens de commit redigidas exclusivamente em **PT-BR**.
- **Sobriedade**: Proibido o uso de emojis em código-fonte, logs ou documentação técnica.
- **Autoexplicabilidade**: Docstrings obrigatórias em PT-BR em módulos, classes e métodos públicos (validadas por `interrogate`).

---

## 2. Universo e Domínio da Aplicação

- **Domínio**: Coleta inteligente e análise estatística de preços de discos de vinil na **Amazon BR (`amazon.com.br`)**.
- **Operação**: Leitura de lista JSON -> Busca de todas as edições/versões de cada álbum -> Filtragem de não-vinis -> Persistência de histórico local (SQLite) + porta extensível externa -> Cálculo de média, mediana, Pré-Black Friday vs. Black Friday e score de custo-benefício -> Exportação JSON + tabela CLI Rich.
- **Arquitetura**: Domain-Driven Design (DDD), Clean Architecture (Ports & Adapters), SOLID e TDD.
- **Quality Gates**: Execução unificada via `scripts/operations/clean_workspace.py` e `Makefile` (`make help`, `app-lint`, `app-validate`, `app-security`, `app-test`, `app-build`, `app-clean`).

---

## 3. Doutrina do Agente: Escopo e Fronteiras Éticas

- **O que o Agente É**: Copiloto generalista de engenharia de software sênior, arquitetura DDD/Clean, QA/TDD e automação CI/CD.
- **O que o Agente NÃO É**: Uma ferramenta para contornar proteções anti-bot. É estritamente proibido tentar resolver, simular ou burlar CAPTCHAs da Amazon BR; bloqueios devem ser reportados via `ScraperBlockedError`.

---

## 4. Harness Canônico Universal (Generalista)

- **Padrão Genérico**: O diretório canônico [`.agents/`](.agents/) padroniza o harness para qualquer ferramenta ou modelo de IA (Antigravity, Cursor, Claude Code, Copilot, etc.), contendo:
  - Agentes generalistas: [`.agents/agents/`](.agents/agents/)
  - Regras universais: [`.agents/rules/`](.agents/rules/)
  - Habilidades especializadas: [`.agents/skills/`](.agents/skills/)
  - Manifesto MCP: [`.agents/mcp.json`](.agents/mcp.json)
- **Rastreabilidade e Matriz**: Cobertura mapeada em [`docs/agent-coverage.md`](docs/agent-coverage.md).

---

## 5. Proibições Globais e Invariantes

- Proibido qualquer import das camadas de `infrastructure` ou `presentation` dentro de `domain` ou `application` (validado via AST no gate `validate`).
- Proibido qualquer arquivo em `src/vinyl_scraper/**/*.py` ultrapassar o teto estrito de **300 linhas** de código.
- Proibido commits ou builds com cobertura de testes abaixo de **100% de branches** (validado via `clean_workspace.py --stage test`).
- Proibido versionar arquivos `.env`, bancos `*.db`/`*.sqlite` ou relatórios em `output/`.
- Proibido mensagens de commit fora do padrão Conventional Commits PT-BR (`linters/commitlint.config.mjs`).
- Proibido afrouxar linters, suprimir checagens de segurança ou utilizar `--no-verify` para forçar commits.

---

## 6. Convenção de Commits (Conventional Commits PT-BR)

- **Formato**: `tipo(escopo): assunto descritivo em PT-BR`
- **Tipos Permitidos**: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `qa`, `refactor`, `revert`, `style`, `test`
- **Escopos Permitidos**: `all`, `app`, `cli`, `config`, `deps`, `domain`, `infra`, `linters`, `parser`, `repo`, `scraper`, `test`

---

## 7. Navegação e Leitura por Tarefa

| Tipo de Tarefa | Arquivo de Leitura Inicial | Skill Recomendada |
|---|---|---|
| Qualquer alteração no repositório | este arquivo + [`docs/agent-coverage.md`](docs/agent-coverage.md) | `surface-sync` |
| Arquitetura DDD, Clean e portas | [`docs/arquitetura.md`](docs/arquitetura.md) + [`docs/structure.md`](docs/structure.md) | `analyze-debug` |
| Qualidade, lint, AST e pre-commit | [`docs/engineering-standards.md`](docs/engineering-standards.md) | `precommit` |
| CI/CD bidirecional e Semantic Release | [`docs/engineering-ci-release.md`](docs/engineering-ci-release.md) | `ci-release` |
| Higienização e Clean Workspace | [`scripts/operations/clean_workspace.py`](scripts/operations/clean_workspace.py) | `repo-hygiene` |
