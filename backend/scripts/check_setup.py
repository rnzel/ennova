# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer / Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting / standalone setup validation
"""Run a local, offline setup check without loading a model or .env file."""
from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

REQUIRED_PACKAGES = (
    ("Flask", "flask"),
    ("Flask-SQLAlchemy", "flask_sqlalchemy"),
    ("Flask-Migrate", "flask_migrate"),
    ("PyMySQL", "pymysql"),
    ("python-dotenv", "dotenv"),
    ("PyJWT", "jwt"),
    ("Flask-Limiter", "flask_limiter"),
    ("SQLAlchemy", "sqlalchemy"),
    ("pytest", "pytest"),
)


def _find_swipl() -> str | None:
    """Locate SWI-Prolog from config and then on PATH, without loading .env."""
    from app.config import BaseConfig

    configured = BaseConfig.SWIPL_EXECUTABLE
    has_override = bool(os.getenv("SWIPL_EXECUTABLE"))
    if has_override:
        discovered = shutil.which(configured)
        if discovered:
            return discovered
        candidate = Path(configured)
        if candidate.is_file():
            return str(candidate)
        return None

    if isinstance(configured, str) and configured.strip():
        discovered = shutil.which(configured)
        if discovered:
            return discovered
        candidate = Path(configured)
        if candidate.is_file():
            return str(candidate)

    return shutil.which("swipl")


def main() -> int:
    """Check local setup and return a process exit status."""
    print(f"Python: {sys.version.split()[0]}")
    success = True

    for label, module_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except Exception:
            print(f"Package {label}: FAIL")
            success = False
        else:
            print(f"Package {label}: PASS")

    executable = _find_swipl()
    if executable is None:
        print("SWI-Prolog executable: NOT FOUND")
        print("SWI-Prolog version: FAIL")
        success = False
    else:
        print(f"SWI-Prolog executable: {executable}")
        try:
            version = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                shell=False,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            print("SWI-Prolog version: FAIL")
            success = False
        else:
            version_text = (
                version.stdout.strip() or version.stderr.strip()
            ).splitlines()
            if version.returncode == 0 and version_text:
                print(f"SWI-Prolog version: {version_text[0]}")
            else:
                print("SWI-Prolog version: FAIL")
                success = False

    if executable is not None:
        try:
            from app.policy import (
                AccessRequest,
                AppFacts,
                EntryFact,
                PrologAccessBridge,
                parse,
            )

            policy = parse(
                "protocol maria:\n"
                '    may read summary of entries tagged "family"\n'
            )
            app_facts = AppFacts(
                registered_people=("maria",),
                death_triggered=True,
                entries=(EntryFact("e_family", "diary"),),
                entry_tags=(("e_family", "family"),),
            )
            requests = (
                AccessRequest(
                    person="maria",
                    entry_id="e_family",
                    level="summary",
                    today=date(2040, 5, 1),
                ),
                AccessRequest(
                    person="maria",
                    entry_id="e_family",
                    level="verbatim",
                    today=date(2040, 5, 1),
                ),
            )
            decisions = PrologAccessBridge(
                executable, timeout_seconds=5.0
            ).can_access_many(policy, app_facts, requests)
        except Exception:
            print("Summary access: FAIL")
            print("Verbatim access: FAIL")
            success = False
        else:
            summary_ok = (
                len(decisions) == 2 and decisions[0] == "allow"
            )
            verbatim_ok = (
                len(decisions) == 2 and decisions[1] == "deny"
            )
            print(f"Summary access: {'PASS' if summary_ok else 'FAIL'}")
            print(f"Verbatim access: {'PASS' if verbatim_ok else 'FAIL'}")
            if not summary_ok or not verbatim_ok:
                success = False

    print(f"OVERALL: {'PASS' if success else 'FAIL'}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
