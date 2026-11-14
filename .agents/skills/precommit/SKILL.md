---
name: precommit
description: Executa e valida os hooks locais bidirecionais de pre-commit e commitlint.
---

# Skill: Pre-commit & Commitlint
Execute via `clean_workspace.py` ou `pre-commit`:
1. `python scripts/operations/clean_workspace.py --area python --stage lint`
2. `python scripts/operations/clean_workspace.py --area python --stage validate`
3. `python scripts/operations/clean_workspace.py --area python --stage security`
4. `python scripts/operations/clean_workspace.py --area python --stage test --coverage-fail-under 100`
5. `python scripts/operations/clean_workspace.py --area python --stage build`
