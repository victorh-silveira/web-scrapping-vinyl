"""Runtime helpers for Clean Workspace quality gates."""

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
    """Print an error message and abort with exit code 1."""
    print(message, file=sys.stderr)
    raise SystemExit(1)


def exit_if_violations(header: str, violations: list[str]) -> None:
    """Print violations and exit if the list is non-empty."""
    if not violations:
        return
    print(f"\n[ERRO] {header}", file=sys.stderr)
    for item in violations:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(1)


def use_repo_cwd() -> None:
    """Ensure working directory is the repository root."""
    os.chdir(REPO_ROOT)


def run_command(cmd: list[str], label: str, cwd: Path | None = None) -> None:
    """Execute a subprocess and fail fast on non-zero exit code."""
    print(f"\n>>> Executando: {label}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or REPO_ROOT, check=False)
    if result.returncode != 0:
        fail(f"[ERRO] Falha em '{label}' (exit code {result.returncode}).")


def run_tool(module: str, args: list[str], label: str) -> None:
    """Execute a Python module tool using the active interpreter."""
    run_command([sys.executable, "-m", module, *args], label)
