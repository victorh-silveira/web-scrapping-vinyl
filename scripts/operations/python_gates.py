"""Gates Python de qualidade, arquitetura, segurança, testes, build e limpeza."""

from __future__ import annotations

import ast
import compileall
import shutil
import subprocess
import sys

from config_gates import stage_json_lint, stage_json_validate, stage_yaml_lint, stage_yaml_validate
from gate_runtime import (
    REPO_ROOT,
    SRC_ROOT,
    exit_if_violations,
    fail,
    run_command,
    run_tool,
)

FORBIDDEN_IMPORTS: dict[str, set[str]] = {
    "domain": {"infrastructure", "presentation", "application"},
    "application": {"infrastructure", "presentation"},
}


def _layer_of_import(module_name: str) -> str | None:
    prefix = "vinyl_scraper."
    if module_name.startswith(prefix):
        rest = module_name[len(prefix) :]
        top = rest.split(".", 1)[0]
        if top in {"domain", "application", "infrastructure", "presentation"}:
            return top
    return None


def stage_lint() -> None:
    """Executa Ruff lint/format, Interrogate docstrings, Vulture código morto e lint YAML/JSON."""
    run_tool("ruff", ["check", "--fix", "src", "tests", "scripts"], "Ruff Check (auto-fix)")
    run_tool("ruff", ["format", "--check", "src", "tests", "scripts"], "Ruff Format Check")
    run_tool("interrogate", ["-vv", "src"], "Interrogate Docstrings")
    run_tool("vulture", [], "Vulture Dead Code Detection")
    stage_yaml_lint()
    stage_json_lint()


def stage_layer_dependencies() -> None:
    """Impõe a direção de dependências da Clean Architecture via inspeção AST."""
    print("\n>>> Executando: Verificacao de dependencias entre camadas (DDD/Clean)")
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        rel = path.relative_to(SRC_ROOT)
        if not rel.parts:
            continue
        layer = rel.parts[0]
        if layer not in FORBIDDEN_IMPORTS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = [node.module]
            for name in imported:
                target = _layer_of_import(name)
                if target and target in FORBIDDEN_IMPORTS[layer]:
                    violations.append(f"{path}: {layer} importa {name}")
    exit_if_violations("Violacao de dependencias entre camadas:", violations)
    print("[OK] Regras de dependencia entre camadas respeitadas.")


def stage_structure(max_lines: int = 300) -> None:
    """Impõe o limite máximo de linhas por arquivo-fonte Python."""
    print(f"\n>>> Executando: Verificacao Estrutural (Max {max_lines} linhas)")
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > max_lines:
            violations.append(f"{path}: {count} linhas")
    exit_if_violations("Violacao de limite de linhas encontrada:", violations)
    print(f"[OK] Todos os arquivos em src/ estao abaixo de {max_lines} linhas.")


def stage_validate() -> None:
    """Executa Mypy strict, gate AST de camadas, teto de linhas e validação YAML/JSON."""
    run_tool("mypy", ["--config-file", "pyproject.toml"], "Mypy Strict")
    stage_layer_dependencies()
    stage_structure(max_lines=300)
    stage_yaml_validate()
    stage_json_validate()


def stage_test(fail_under: int = 100) -> None:
    """Executa pytest com exigência de cobertura de branches."""
    run_tool("coverage", ["run", "--branch", "-m", "pytest"], "Pytest (branch coverage)")
    run_tool(
        "coverage",
        ["report", f"--fail-under={fail_under}"],
        f"Coverage report (min {fail_under}%)",
    )


def stage_security() -> None:
    """Executa Bandit SAST, pip-audit de dependências e Gitleaks para segredos."""
    run_tool("bandit", ["-r", "src", "-c", "pyproject.toml"], "Bandit Security Scan")
    run_tool("pip_audit", [], "Pip-audit Vulnerability Scan")
    gitleaks = shutil.which("gitleaks")
    if gitleaks is None:
        print("[OK] Gitleaks nao encontrado no PATH; pulado localmente.")
        return
    run_command(
        [gitleaks, "detect", "--source", str(REPO_ROOT), "--verbose", "--redact"],
        "Gitleaks Secret Scan",
        cwd=REPO_ROOT,
    )


def stage_build() -> None:
    """Compila todos os arquivos-fonte Python para bytecode."""
    print("\n>>> Executando: compileall")
    if not compileall.compile_dir(str(SRC_ROOT), quiet=1):
        fail(f"[ERRO] Falha no compileall: {SRC_ROOT}")
    print("[OK] compileall concluido.")


def stage_clean() -> None:
    """Remove caches locais, artefatos de cobertura e diretórios temporários de build."""
    print("\n>>> Executando: Clean Workspace")
    cache_dirs = (".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", "htmlcov")
    for name in cache_dirs:
        target = REPO_ROOT / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    for pycache in REPO_ROOT.rglob("__pycache__"):
        if ".venv" not in pycache.parts:
            shutil.rmtree(pycache, ignore_errors=True)
    cov_file = REPO_ROOT / ".coverage"
    if cov_file.exists():
        cov_file.unlink()
    print("[OK] Workspace limpo.")


def format_all() -> None:
    """Utilitário para autoformatar arquivos-fonte com o Ruff."""
    subprocess.run([sys.executable, "-m", "ruff", "format", "src", "tests", "scripts"], check=True)
