"""Utilitários de execução para os quality gates do Clean Workspace."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

OPERATIONS_DIR = Path(__file__).resolve().parent
REPO_ROOT = OPERATIONS_DIR.parent.parent
SRC_ROOT = REPO_ROOT / "src" / "vinyl_scraper"
TESTS_ROOT = REPO_ROOT / "tests"

AREAS = ("python",)
STAGES = ("lint", "validate", "security", "test", "pytest", "build", "clean")
AREA_STAGES: dict[str, tuple[str, ...]] = {
    "python": STAGES,
}


def fail(message: str) -> None:
    """Exibe uma mensagem de erro e aborta com código de saída 1."""
    print(message, file=sys.stderr)
    raise SystemExit(1)


def exit_if_violations(header: str, violations: list[str]) -> None:
    """Exibe as violações e encerra caso a lista não esteja vazia."""
    if not violations:
        return
    print(f"\n[ERRO] {header}", file=sys.stderr)
    for item in violations:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(1)


def use_repo_cwd() -> None:
    """Garante que o diretório de trabalho seja a raiz do repositório."""
    os.chdir(REPO_ROOT)


def run_command(cmd: list[str], label: str, cwd: Path | None = None) -> None:
    """Executa um subprocesso e falha imediatamente em código de saída diferente de zero."""
    print(f"\n>>> Executando: {label}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or REPO_ROOT, check=False)
    if result.returncode != 0:
        fail(f"[ERRO] Falha em '{label}' (exit code {result.returncode}).")


def run_tool(module: str, args: list[str], label: str) -> None:
    """Executa uma ferramenta de módulo Python usando o interpretador ativo."""
    run_command([sys.executable, "-m", module, *args], label)
