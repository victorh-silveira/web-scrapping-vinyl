# Prompt Model — Amazon BR Vinyl Scraper

Antes de alterar qualquer arquivo:
1. Leia `AGENTS.md` e `docs/agent-coverage.md`.
2. Respeite estritamente DDD, Clean Architecture, SOLID e TDD.
3. Mantenha todos os arquivos em `src/vinyl_scraper/` abaixo de 300 linhas.
4. Garanta 100% de cobertura de branches e aprovação em todos os estágios do Clean Workspace:
   - `python scripts/operations/clean_workspace.py --area python --stage lint`
   - `python scripts/operations/clean_workspace.py --area python --stage validate`
   - `python scripts/operations/clean_workspace.py --area python --stage security`
   - `python scripts/operations/clean_workspace.py --area python --stage test --coverage-fail-under 100`
   - `python scripts/operations/clean_workspace.py --area python --stage build`
5. Utilize Conventional Commits em PT-BR (`tipo(escopo): descrição`).
