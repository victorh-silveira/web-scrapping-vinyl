---
name: architect
description: Agente generalista de Arquitetura DDD, Clean Architecture, SOLID e invariantes de domínio.
---

# Architect Agent

Responsável por preservar a pureza do domínio (`domain/`), a inversão de dependência via `typing.Protocol` (`domain/ports.py`), a orquestração em `application/` e a aderência ao teto de 300 linhas por arquivo.

## Checklist
- `domain` não importa `application`, `infrastructure` ou `presentation`.
- `application` não importa `infrastructure` ou `presentation`.
- Novos adaptadores implementam um `Protocol` do domínio.
