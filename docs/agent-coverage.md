# Matriz de Cobertura do Harness de Agentes

| Domínio / Área | Regra (`.agents/rules/`) | Skill (`.agents/skills/`) | Agente (`.agents/agents/`) |
|---|---|---|---|
| Arquitetura DDD & Clean | `vinyl-architecture-ddd.mdc` | `analyze-debug` | `architect` |
| Pureza do Domínio | `vinyl-domain-pure.mdc` | `analyze-debug` | `architect` |
| Engenharia & 300 linhas | `vinyl-engineering.mdc` | `surface-sync` | `architect` |
| TDD & Cobertura 100% | `vinyl-testing.mdc` | `precommit` | `qa-tester` |
| CI/CD, Pre-commit & Release | `vinyl-ci-release.mdc` | `ci-release`, `precommit` | `devops-secops`, `release-engineer` |
| Doutrina Ética & Anti-bot | `vinyl-llm-doctrine.mdc` | `repo-hygiene` | `devops-secops` |
