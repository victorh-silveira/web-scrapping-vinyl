"""JSON and YAML lint/validation gates."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from gate_runtime import REPO_ROOT, exit_if_violations, run_tool

_IGNORED_DIRS = {
    ".venv",
    "venv",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}


def _iter_files(extensions: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in extensions:
            files.append(path)
    return sorted(files)


def stage_json_lint() -> None:
    """Validate JSON syntax across repository files."""
    stage_json_validate()


def stage_json_validate() -> None:
    """Parse all JSON files in the repository to ensure valid syntax."""
    print("\n>>> Executando: JSON Validate")
    violations: list[str] = []
    for path in _iter_files((".json",)):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append(f"{path}: {exc}")
    exit_if_violations("Arquivos JSON invalidos:", violations)
    print("[OK] Todos os arquivos JSON sao validos.")


def stage_yaml_lint() -> None:
    """Run yamllint on repository YAML files."""
    yaml_files = [str(p.relative_to(REPO_ROOT)) for p in _iter_files((".yml", ".yaml"))]
    if not yaml_files:
        print("[OK] Nenhum arquivo YAML encontrado.")
        return
    run_tool("yamllint", ["-c", ".yamllint.yaml", *yaml_files], "Yamllint")


def stage_yaml_validate() -> None:
    """Parse all YAML files using PyYAML safe_load."""
    print("\n>>> Executando: YAML Validate")
    violations: list[str] = []
    for path in _iter_files((".yml", ".yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append(f"{path}: {exc}")
    exit_if_violations("Arquivos YAML invalidos:", violations)
    print("[OK] Todos os arquivos YAML sao validos.")
