# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Required test infrastructure for SWI-Prolog integration
import os
import shutil
from pathlib import Path

import pytest


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
