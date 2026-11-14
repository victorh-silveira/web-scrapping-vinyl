# CI/CD Bidirecional & Semantic Release

## Paridade Bidirecional (Local <-> CI)

O arquivo `linters/pre-commit-config.yaml` (espelhado em `.pre-commit-config.yaml`) e o workflow `.github/workflows/ci.yml` invocam exatamente os mesmos comandos do `scripts/operations/clean_workspace.py`. Isso garante que qualquer commit aprovado localmente passe no CI sem surpresas.

## Conventional Commits & Semantic Release

- Commits validados pelo `commitlint` (`linters/commitlint.config.mjs`) no estágio `commit-msg`.
- Na branch `main`, após aprovação dos jobs `python` e `workflows`, o job `release` executa o `semantic-release` (`linters/releaserc.json`), gerando tags SemVer, GitHub Releases e atualizando `docs/CHANGELOG.md`.
