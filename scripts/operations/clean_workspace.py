"""Single Source of Truth (SSOT) Quality Gate Runner for local and CI execution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

OPERATIONS = Path(__file__).resolve().parent
if str(OPERATIONS) not in sys.path:
    sys.path.insert(0, str(OPERATIONS))

from gate_runtime import AREA_STAGES, AREAS, STAGES, fail, use_repo_cwd  # noqa: E402
from python_gates import (  # noqa: E402
    stage_build,
    stage_clean,
    stage_lint,
    stage_security,
    stage_test,
    stage_validate,
)


def _dispatch(area: str, stage: str, coverage_fail_under: int) -> None:
    if area not in AREA_STAGES:
        fail(f"[ERRO] Area '{area}' nao suportada")
    if stage == "clean":
        stage_clean()
        return
    if stage not in AREA_STAGES[area]:
        fail(f"[ERRO] Stage '{stage}' nao suportado para area '{area}'")
    if stage == "lint":
        stage_lint()
    elif stage == "validate":
        stage_validate()
    elif stage == "security":
        stage_security()
    elif stage in {"test", "pytest"}:
        stage_test(coverage_fail_under)
    else:
        stage_build()


def main() -> None:
    """Parse CLI arguments and execute the requested quality gate stage."""
    parser = argparse.ArgumentParser(description="Vinyl Scraper Clean Workspace Quality Gate")
    parser.add_argument("--area", choices=AREAS, default="python")
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--coverage-fail-under", type=int, default=100)
    args = parser.parse_args()
    use_repo_cwd()
    _dispatch(args.area, args.stage, args.coverage_fail_under)
    print("\n[SUCESSO] Estagio concluido com sucesso.")


if __name__ == "__main__":
    main()
