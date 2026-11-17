# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Required test infrastructure for SWI-Prolog integration
import os
import shutil
from pathlib import Path

import pytest

if os.getenv("RUN_LIVE_AI_TESTS") == "1":
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parents[1] / ".env")


@pytest.fixture(scope="session")
def swipl_executable() -> str:
    """Find SWI-Prolog or fail the suite because F5/F6a require it."""
    configured = os.getenv("SWIPL_EXECUTABLE")
    if configured:
        executable = shutil.which(configured) or configured
        if Path(executable).is_file():
            return executable
    discovered = shutil.which("swipl")
    if discovered:
        return discovered
    program_files = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
    windows_executable = program_files / "swipl" / "bin" / "swipl.exe"
    if windows_executable.is_file():
        return str(windows_executable)
    pytest.fail("SWI-Prolog is required for F5/F6a tests but was not found.")
