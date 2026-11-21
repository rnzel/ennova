# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting orchestration with Prolog-authorized grounded answers
"""Run the handout's Maria acceptance questions against the fictional fixture."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

from app.ai.client import (
    FakeModelClient,
    ModelClient,
    ModelPrompt,
    ModelResponse,
    PromptMessage,
    ToolCall,
)
from app.ai.ollama import _estimate_prompt_tokens, _serialize_request
from app.ai.citations import GroundedResponse
from app.ai.tools import EntryView
from app.ai.prompts import NEUTRAL_REPLY
from app.ai.provider import create_model_client
from app.ai.summaries import (
    FakeSummarizer,
    InMemorySummaryStore,
    store_derived_summary,
)
from app.domain.diary import InMemoryEntryRepository, StoredEntry
from app.domain.processing import PersonReference
from app.errors import AIServiceUnavailable, EnnovaError, GENERIC_PUBLIC_MESSAGE
from app.policy import AppFacts, PrologAccessBridge
from app.services.access_facts import build_app_facts
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService

POLICY_PATH = PROJECT_DIR / "docs" / "grammar" / "sample_maria.policy"
OWNER_ID = "owner-lola"
MARIA_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("existence", "Did he ever write about me?"),
    ("family", "What did he write about family?"),
    ("letter", "Show me the letter to my daughter"),
    ("business", "What did he think about his business?"),
    ("nora", "What is in the diary?"),
)
EXPECTED = {
    "existence": "existence count",
    "family": "family summary with dates",
    "letter_before": "date message before 2040-05-01",
    "letter_after": "verbatim letter on/after 2040-05-01",
    "business": "neutral reply",
    "nora": "identical neutral reply (no protocol)",
}


class DemoError(Exception):
    """A safe, one-line command-line failure."""

    def __init__(self, message: str) -> None:
        self.public_message = message
        super().__init__(message)


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser errors into the demo's safe one-line error boundary."""

    def error(self, message: str) -> None:
        raise DemoError(f"Invalid command-line arguments: {message}.")


@dataclass
class CallMetric:
    """Safe timing and size data for one model call."""

    prompt_tokens: int
    elapsed: float
    tools: list["ToolMetric"]


@dataclass
class ToolMetric:
    """Safe metadata for one requested tool call."""

    name: str
    arguments_valid: bool
    permitted_result: bool = False
    neutral_or_empty: bool = False
    repeated: bool = False
    request_count: int = 1


@runtime_checkable
class _InspectableModel(Protocol):
    """Model attributes needed to reproduce Ollama's request estimator."""

    _model: str
    _num_ctx: int
    _max_output_tokens: int


class InstrumentedModelClient:
    """Record model-call timing and prompt sizes without recording content."""

    def __init__(self, client: ModelClient) -> None:
        self._client = client
        self.metrics: list[CallMetric] = []
        self._pending_tools: list[ToolMetric] = []
        self._tool_counts: dict[str, int] = {}
        self.question_timeout_seconds = getattr(
            client, "question_timeout_seconds", 45.0
        )

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        """Delegate one call while retaining only safe size and timing metrics."""
        started = time.monotonic()
        try:
            response = self._client.complete(prompt)
            tools = [
                self._new_tool_metric(call) for call in response.tool_calls
            ]
            self._pending_tools = tools.copy()
            return response
        finally:
            self.metrics.append(
                CallMetric(
                    self._estimate(prompt),
                    time.monotonic() - started,
                    locals().get("tools", []),
                )
            )

    def _new_tool_metric(self, call: ToolCall) -> ToolMetric:
        name = call.name if isinstance(call, ToolCall) else ""
        signature = self._signature(call)
        count = self._tool_counts.get(signature, 0) + 1
        self._tool_counts[signature] = count
        return ToolMetric(
            name=name or "unknown",
            arguments_valid=_valid_tool_call(call),
            repeated=count > 1,
            request_count=count,
        )

    @staticmethod
    def _signature(call: ToolCall) -> str:
        arguments = call.arguments if isinstance(call, ToolCall) else None
        return json.dumps(
            [
                call.name if isinstance(call, ToolCall) else "",
                arguments,
            ],
            ensure_ascii=False,
            sort_keys=True,
            default=repr,
        )

    def observe_tool_result(self, result: object) -> None:
        """Attach only safe result classification to the next tool request."""
        if not self._pending_tools:
            return
        metric = self._pending_tools.pop(0)
        metric.permitted_result = _is_permitted_result(result)
        metric.neutral_or_empty = _is_neutral_or_empty(result)

    def _estimate(self, prompt: ModelPrompt) -> int:
        client = self._client
        if not all(
            hasattr(client, attribute)
            for attribute in ("_model", "_num_ctx", "_max_output_tokens")
        ):
            return 0
        inspectable = client
        if not isinstance(inspectable, _InspectableModel):
            return 0
        body = _serialize_request(
            prompt,
            inspectable._model,
            inspectable._num_ctx,
            inspectable._max_output_tokens,
        )
        return _estimate_prompt_tokens(body)


def _valid_tool_call(call: object) -> bool:
    """Mirror the service dispatcher’s argument-shape validation."""
    if not isinstance(call, ToolCall) or not isinstance(call.name, str):
        return False
    if not isinstance(call.arguments, Mapping):
        return False
    expected = {
        "search_entries": "query",
        "get_entry": "entry_id",
        "count_mentions": "name",
        "get_letter": "title",
    }.get(call.name)
    if expected is None or set(call.arguments) != {expected}:
        return False
    return isinstance(call.arguments[expected], str)


def _is_permitted_result(result: object) -> bool:
    """Classify only results that contain permitted content or a count."""
    if isinstance(result, EntryView):
        return True
    if isinstance(result, int):
        return result > 0
    if isinstance(result, tuple):
        return any(isinstance(item, EntryView) for item in result)
    return False


def _is_neutral_or_empty(result: object) -> bool:
    """Classify empty, denied, or neutral tool results without their content."""
    if result is None or result == ():
        return True
    return isinstance(result, GroundedResponse) and result.text == NEUTRAL_REPLY


class InstrumentedGroundedQAService(GroundedQAService):
    """Observe tool metadata while preserving the grounded service behavior."""

    def __init__(
        self,
        *args: object,
        instrumented_model: InstrumentedModelClient,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._instrumented_model = instrumented_model

    def _execute_tool(self, call: object, context: object) -> object | None:
        result = super()._execute_tool(call, context)
        self._instrumented_model.observe_tool_result(result)
        return result


@dataclass(frozen=True)
class DemoFixture:
    """Fictional Lola fixture and its immutable application facts."""

    service: DiaryService
    records: tuple[StoredEntry, ...]
    app_facts: AppFacts
    summaries: InMemorySummaryStore


def build_fixture() -> DemoFixture:
    """Build the fictional fixture without reading the clock or environment."""
    service = DiaryService(InMemoryEntryRepository())
    people = (
        PersonReference("beneficiary-maria", "Maria"),
        PersonReference("beneficiary-nora", "Nora"),
    )
    timestamps = tuple(
        datetime(2026, 11, 14, hour, tzinfo=timezone.utc)
        for hour in range(9, 14)
    )
    records = (
        service.add_diary_entry(
            OWNER_ID,
            "e_maria",
            "Lola remembers visiting [[Maria]] beside the garden.",
            timestamps[0],
            people,
        ),
        service.add_diary_entry(
            OWNER_ID,
            "e_family",
            "The fictional family shared soup with [[Maria]]. #family",
            timestamps[1],
            people,
        ),
        service.add_diary_entry(
            OWNER_ID,
            "e_family_2",
            "A quiet family supper at home. #family",
            timestamps[2],
            people,
        ),
        service.add_diary_entry(
            OWNER_ID,
            "e_business",
            "Lola reviewed the orchard shop ledger. #business",
            timestamps[3],
            people,
        ),
        service.add_letter_entry(
            OWNER_ID,
            "e_letter",
            "My dearest daughter, remember this small story about kindness.",
            "To my daughter",
            "Maria",
            timestamps[4],
            people,
        ),
    )
    summaries = InMemorySummaryStore()
    summarizer = FakeSummarizer()
    for record in records:
        store_derived_summary(record, summarizer, summaries)
    return DemoFixture(
        service,
        records,
        build_app_facts(
            OWNER_ID,
            records,
            ("Maria", "Nora"),
            death_triggered=True,
            policy_frozen=True,
        ),
        summaries,
    )


def _fake_client(question: str, asker: str, today: date) -> FakeModelClient:
    """Return a deterministic fake response sequence for one safe demo row."""
    folded = question.casefold()
    if asker == "maria" and "ever write about me" in folded:
        return FakeModelClient(
            (ModelResponse("", tool_calls=(ToolCall("count_mentions", {"name": "maria"}),)),)
        )
    if asker == "maria" and "family" in folded:
        return FakeModelClient(
            (
                ModelResponse("", tool_calls=(ToolCall("search_entries", {"query": "family"}),)),
                ModelResponse(
                    "The permitted family records are summarized below.",
                    citation_ids=("e_family", "e_family_2"),
                ),
            )
        )
    if asker == "maria" and "letter" in folded and today >= date(2040, 5, 1):
        return FakeModelClient(
            (
                ModelResponse("", tool_calls=(ToolCall("get_letter", {"title": "To my daughter"}),)),
                ModelResponse(
                    "My dearest daughter, remember this small story about kindness.",
                    citation_ids=("e_letter",),
                ),
            )
        )
    if asker == "maria" and "business" in folded:
        return FakeModelClient(
            (
                ModelResponse(
                    "",
                    tool_calls=(ToolCall("get_entry", {"entry_id": "e_business"}),),
                ),
            )
        )
    return FakeModelClient(())


def _swipl() -> str:
    """Find SWI-Prolog without exposing configured paths."""
    configured = os.getenv("SWIPL_EXECUTABLE")
    if configured:
        executable = shutil.which(configured) or configured
        if Path(executable).is_file():
            return executable
    executable = shutil.which("swipl")
    if executable:
        return executable
    program_files = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
    executable = program_files / "swipl" / "bin" / "swipl.exe"
    if executable.is_file():
        return str(executable)
    raise DemoError("SWI-Prolog is required to run the Maria demo.")


def _parse_date(value: str) -> date:
    """Parse one ISO date and expose only a safe validation message."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise DemoError("Invalid date: use YYYY-MM-DD.") from error


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(add_help=True)
    parser.add_argument("--today", help="Run every row at one YYYY-MM-DD date.")
    parser.add_argument("--as", dest="asker", choices=("maria", "nora"), default="maria")
    parser.add_argument("--ask", help="Run one red-team question instead of the six rows.")
    parser.add_argument(
        "--verbose-errors",
        action="store_true",
        help="Show only exception class and code for unavailable rows.",
    )
    return parser


def _print_response(
    label: str,
    question: str,
    expected: str,
    response: GroundedResponse,
    today: date,
    elapsed: float,
) -> None:
    """Print only the public response and backend-verified citations."""
    print(f"\n[{label}] {question}")
    print(f"Expected behavior: {expected}")
    print(f"Today: {today.isoformat()}")
    print(f"Reply: {response.text}")
    if response.disclaimer is not None:
        print(f"Disclaimer: {response.disclaimer}")
    if response.citations:
        citations = ", ".join(
            f"{citation.entry_id} ({citation.entry_date.isoformat()})"
            for citation in response.citations
        )
        print(f"Citations: {citations}")
    else:
        print("Citations: none")
    print(f"Elapsed: {elapsed:.3f}s")


def _print_unavailable(
    label: str,
    question: str,
    expected: str,
    today: date,
    elapsed: float,
    error: AIServiceUnavailable,
    verbose_errors: bool,
    metrics: tuple[CallMetric, ...],
) -> None:
    """Print a safe unavailable row and optional typed diagnostics."""
    print(f"\n[{label}] {question}")
    print(f"Expected behavior: {expected}")
    print(f"Today: {today.isoformat()}")
    print("Reply: unavailable")
    print("Citations: none")
    if verbose_errors:
        _print_metrics(metrics)
        provider_class, provider_code = _provider_failure(error)
        print(f"Provider failure: {provider_class} {provider_code}")
    print(f"Elapsed: {elapsed:.3f}s")


def _print_metrics(metrics: tuple[CallMetric, ...]) -> None:
    """Print model-call count and safe per-call measurements."""
    print(f"Model calls: {len(metrics)}")
    for index, metric in enumerate(metrics, start=1):
        print(
            f"Call {index}: prompt tokens {metric.prompt_tokens}; "
            f"elapsed {metric.elapsed:.3f}s"
        )
        if not metric.tools:
            print("  Tool: none; count 0")
        for tool in metric.tools:
            print(
                f"  Tool: {tool.name}; arguments_valid={tool.arguments_valid}; "
                f"permitted_result={tool.permitted_result}; "
                f"neutral_or_empty={tool.neutral_or_empty}; "
                f"repeated={tool.repeated}; count={tool.request_count}"
            )


def _provider_failure(error: AIServiceUnavailable) -> tuple[str, str]:
    """Extract only provider class/code fields from private error detail."""
    detail = error.detail
    if isinstance(detail, dict):
        exception_class = detail.get("exception_class")
        code = detail.get("code")
        if isinstance(exception_class, str) and isinstance(code, str):
            return exception_class, code
    return type(error).__name__, error.code


def _warm_up(model: object) -> float:
    """Send one tiny request before timing the demonstration questions."""
    prompt = ModelPrompt(
        "Reply with OK only.",
        (PromptMessage("user", "OK"),),
        (),
    )
    started = time.monotonic()
    model.complete(prompt)
    return time.monotonic() - started


def _run(args: argparse.Namespace) -> bool:
    """Run the selected demo rows with a caller-supplied date."""
    if not POLICY_PATH.is_file():
        raise DemoError("The Maria policy fixture is unavailable.")
    today_override = _parse_date(args.today) if args.today is not None else None
    swipl = _swipl()
    policy_source = POLICY_PATH.read_text(encoding="utf-8")
    fixture = build_fixture()
    provider = os.getenv("LLM_PROVIDER", "").strip().casefold()
    if provider not in {"ollama", "fake"}:
        raise AIServiceUnavailable()
    model_name = os.getenv("OLLAMA_MODEL", "").strip()
    warmup_unavailable = False
    if provider == "ollama":
        if not model_name:
            raise AIServiceUnavailable()
        print(f"Provider: ollama (model: {model_name})")
        model = create_model_client()
        try:
            print(f"Warm-up load time: {_warm_up(model):.3f}s")
        except AIServiceUnavailable as error:
            warmup_unavailable = True
            print("Warm-up load time: unavailable")
            if args.verbose_errors:
                print(f"Warm-up error: {type(error).__name__} ({error.code})")
    else:
        print("Provider: SCRIPTED (fake model)")
        model = None
        print("Warm-up load time: not applicable (scripted fake model)")

    bridge = PrologAccessBridge(swipl, timeout_seconds=5.0)
    if args.ask is not None:
        rows = (("red-team", args.ask, "permission-filtered answer"),)
    else:
        rows = (
            ("existence", MARIA_QUESTIONS[0][1], EXPECTED["existence"]),
            ("family", MARIA_QUESTIONS[1][1], EXPECTED["family"]),
            ("letter-before", MARIA_QUESTIONS[2][1], EXPECTED["letter_before"]),
            ("letter-after", MARIA_QUESTIONS[2][1], EXPECTED["letter_after"]),
            ("business", MARIA_QUESTIONS[3][1], EXPECTED["business"]),
            ("nora", MARIA_QUESTIONS[4][1], EXPECTED["nora"]),
        )
    row_unavailable = False
    for label, question, expected in rows:
        asker = args.asker if args.ask is not None else (
            "nora" if label == "nora" else "maria"
        )
        dates = (
            (today_override,)
            if today_override is not None
            else (
                (date(2040, 4, 30),)
                if label == "letter-before"
                else (date(2040, 5, 1),)
                if label == "letter-after"
                else (date.today(),)
            )
        )
        for today in dates:
            question_model = (
                create_model_client(
                    fake_client=_fake_client(question, asker, today)
                )
                if provider == "fake"
                else model
            )
            instrumented_model = InstrumentedModelClient(question_model)
            service = InstrumentedGroundedQAService(
                fixture.service,
                bridge,
                instrumented_model,
                fixture.summaries,
                instrumented_model=instrumented_model,
            )
            started = time.monotonic()
            try:
                response = service.answer(
                    question,
                    owner_id=OWNER_ID,
                    asker=asker,
                    policy_source=policy_source,
                    app_facts=fixture.app_facts,
                    today=today,
                )
            except AIServiceUnavailable as error:
                row_unavailable = True
                _print_unavailable(
                    label,
                    question,
                    expected,
                    today,
                    time.monotonic() - started,
                    error,
                    args.verbose_errors,
                    tuple(instrumented_model.metrics),
                )
                continue
            if args.verbose_errors:
                _print_metrics(tuple(instrumented_model.metrics))
            _print_response(
                label, question, expected, response, today,
                time.monotonic() - started,
            )
    return row_unavailable or warmup_unavailable


def main(argv: list[str] | None = None) -> int:
    """Run the demo and convert all failures into safe one-line output."""
    try:
        load_dotenv(BACKEND_DIR / ".env")
        return int(_run(_parser().parse_args(argv)))
    except EnnovaError as error:
        print(error.public_message, file=sys.stderr)
    except DemoError as error:
        print(error.public_message, file=sys.stderr)
    except (OSError, TypeError, ValueError):
        print(GENERIC_PUBLIC_MESSAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
