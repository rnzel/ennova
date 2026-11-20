# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting setup-check tests
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "check_setup.py"


def _run_script(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the setup check from the backend working directory."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT / "backend",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_check_setup_passes_with_required_packages_and_swipl(
    swipl_executable: str,
):
    environment = os.environ.copy()
    environment["SWIPL_EXECUTABLE"] = swipl_executable

    result = _run_script(environment)

    assert result.returncode == 0
    assert "Python:" in result.stdout
    assert "Package Flask: PASS" in result.stdout
    assert "SWI-Prolog version:" in result.stdout
    assert "Summary access: PASS" in result.stdout
    assert "Verbatim access: PASS" in result.stdout
    assert "OVERALL: PASS" in result.stdout


def test_check_setup_fails_without_swipl_not_skips():
    environment = os.environ.copy()
    environment["SWIPL_EXECUTABLE"] = "definitely-missing-swipl-executable"

    result = _run_script(environment)

    assert result.returncode != 0
    assert "SWI-Prolog executable: NOT FOUND" in result.stdout
    assert "SWI-Prolog version: FAIL" in result.stdout
    assert "OVERALL: FAIL" in result.stdout
