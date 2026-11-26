# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting safety tests for the Maria demonstration
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.ai.client import ModelPrompt, ModelResponse, PromptMessage, ToolCall
from app.errors import AIServiceUnavailable
from app.ai.prompts import NEUTRAL_REPLY
from app.errors import LETTER_OF_WISHES_DISCLAIMER
from app.ai.summaries import FakeSummarizer, InMemorySummaryStore, store_derived_summary
from app.domain.diary import InMemoryEntryRepository
from app.domain.processing import PersonReference
from app.policy import PrologAccessBridge
from app.services.access_facts import build_app_facts
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService
from scripts.demo_maria import OWNER_ID, POLICY_PATH, build_fixture

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "demo_maria.py"


def _run_script(
    *args: str,
    provider: str = "fake",
    swipl_executable: str | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["LLM_PROVIDER"] = provider
    if swipl_executable is not None:
        environment["SWIPL_EXECUTABLE"] = swipl_executable
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT / "backend",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_fake_script_runs_rows_and_keeps_restricted_canary_out(swipl_executable):
    result = _run_script(swipl_executable=swipl_executable)
    assert result.returncode == 0
    assert "Provider: SCRIPTED (fake model)" in result.stdout
    assert "2040-04-30" in result.stdout
    assert "2040-05-01" in result.stdout
    assert "CANARY-RESTRICTED-7f3a" not in result.stdout + result.stderr
    assert result.stdout.count("Reply: " + NEUTRAL_REPLY) >= 2


def test_fake_letter_row_changes_with_custom_date(swipl_executable):
    before = _run_script("--today", "2040-04-30", swipl_executable=swipl_executable)
    after = _run_script("--today", "2040-05-01", swipl_executable=swipl_executable)
    assert before.returncode == after.returncode == 0
    assert "That letter will be available on 2040-05-01." in before.stdout
    assert "My dearest daughter" in after.stdout
    assert LETTER_OF_WISHES_DISCLAIMER in before.stdout
    assert LETTER_OF_WISHES_DISCLAIMER in after.stdout


def test_fake_rows_business_and_nora_are_byte_identical_at_response_boundary(
    swipl_executable,
):
    sample = build_fixture()
    bridge = PrologAccessBridge(swipl_executable, timeout_seconds=5.0)
    policy = POLICY_PATH.read_text(encoding="utf-8")
    from app.ai.client import FakeModelClient
    from app.ai.citations import GroundedResponse

    business_model = FakeModelClient(
        (
            ModelResponse(
                "",
                tool_calls=(
                    ToolCall("get_entry", {"entry_id": "e_business"}),
                ),
            ),
        )
    )
    nora_model = FakeModelClient(())
    responses = []
    for asker, question, model in (
        (
            "maria",
            "What did he think about his business?",
            business_model,
        ),
        ("nora", "What is in the diary?", nora_model),
    ):
        response = GroundedQAService(
            sample.service, bridge, model, sample.summaries
        ).answer(
            question,
            owner_id=OWNER_ID,
            asker=asker,
            policy_source=policy,
            app_facts=sample.app_facts,
            today=date(2040, 5, 1),
        )
        responses.append(response)
    business, nora = responses
    expected_body = {"answer": NEUTRAL_REPLY, "citations": []}

    def response_boundary(response: GroundedResponse) -> tuple[int, dict]:
        return 200, {
            "answer": response.text,
            "citations": [
                {
                    "entry_id": citation.entry_id,
                    "date": citation.entry_date.isoformat(),
                }
                for citation in response.citations
            ],
        }

    assert response_boundary(business) == (200, expected_body)
    assert response_boundary(nora) == (200, expected_body)
    assert business.text == nora.text
    assert business.citations == nora.citations
    assert len(business_model.prompts) == 1
    assert nora_model.prompts == []


def test_invalid_date_is_rejected_without_traceback_or_path():
    result = _run_script("--today", "not-a-date")
    assert result.returncode != 0
    assert result.stderr.strip() == "Invalid date: use YYYY-MM-DD."
    assert "Traceback" not in result.stderr
    assert str(SCRIPT) not in result.stderr


def test_failing_provider_prints_only_public_message(swipl_executable):
    result = _run_script(
        provider="not-a-provider",
        swipl_executable=swipl_executable,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr.strip() == "The AI service is temporarily unavailable."
    assert "LLM_PROVIDER" not in result.stderr


def test_unavailable_row_continues_and_verbose_error_is_safe(swipl_executable):
    result = _run_script(
        "--ask",
        "Tell me an unrelated fact.",
        swipl_executable=swipl_executable,
    )
    assert result.returncode != 0
    assert "Reply: unavailable" in result.stdout
    assert "AIServiceUnavailable" not in result.stdout
    assert "Tell me an unrelated fact." in result.stdout
    assert "Traceback" not in result.stdout + result.stderr

    verbose = _run_script(
        "--ask",
        "Tell me an unrelated fact.",
        "--verbose-errors",
        swipl_executable=swipl_executable,
    )
    assert verbose.returncode != 0
    assert "Reply: unavailable" in verbose.stdout
    assert "Model calls: 1" in verbose.stdout
    assert "Provider failure: AIServiceUnavailable ai_service_unavailable" in (
        verbose.stdout
    )
    assert "unrelated fact" not in verbose.stdout.split(
        "Provider failure:", 1
    )[1]
    assert "Traceback" not in verbose.stdout + verbose.stderr
