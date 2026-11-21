# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Grounded AI orchestration and fail-closed service glue
from __future__ import annotations

import json
import time
from collections.abc import Mapping
from datetime import date, datetime

from app.ai.citations import GroundedResponse, attach_citations
from app.ai.client import (
    ModelClient,
    ModelPrompt,
    ModelResponse,
    PromptMessage,
    ToolCall,
)
from app.ai.prompts import (
    LETTER_NOT_YET_MESSAGE,
    NEUTRAL_REPLY,
    SYSTEM_PROMPT,
    TOOL_NAMES,
    render_untrusted_block,
)
from app.ai.summaries import SummaryStore
from app.ai.tools import (
    EntryView,
    ToolContext,
    count_mentions,
    get_entry,
    get_letter,
    search_entries,
    verify_entry,
)
from app.domain.diary import LetterEntry, StoredEntry
from app.errors import (
    AIServiceUnavailable,
    AccessDenied,
    AmbiguousName,
    PolicyFrozen,
    PolicySyntaxError,
    TamperDetected,
)
from app.policy import (
    AccessBatchResult,
    AccessLevel,
    AccessRequest,
    AppFacts,
    LetterStatus,
    LetterStatusRequest,
    Policy,
    PrologAccessBridge,
    ReleaseLetter,
    parse,
)
from app.services.diary_service import DiaryService

_LEVELS: tuple[AccessLevel, ...] = ("existence", "summary", "verbatim")
_MAX_TOOL_STEPS = 5
_DEFAULT_QUESTION_TIMEOUT_SECONDS = 45.0


class GroundedQAService:
    """Resolve permissions once, then orchestrate only permitted model inputs."""

    def __init__(
        self,
        diary_service: DiaryService,
        bridge: PrologAccessBridge,
        model_client: ModelClient,
        summary_store: SummaryStore,
        max_tool_steps: int = _MAX_TOOL_STEPS,
    ) -> None:
        """Create a grounded-answer service without a network model dependency."""
        if max_tool_steps < 1:
            raise ValueError("max_tool_steps must be at least one.")
        self._diary_service = diary_service
        self._bridge = bridge
        self._model_client = model_client
        self._summary_store = summary_store
        self._max_tool_steps = max_tool_steps

    def answer(
        self,
        question: str,
        *,
        owner_id: str,
        asker: str,
        policy_source: str,
        app_facts: AppFacts,
        today: date,
    ) -> GroundedResponse:
        """Answer one beneficiary question, failing closed on every error."""
        try:
            timeout = getattr(
                self._model_client,
                "question_timeout_seconds",
                _DEFAULT_QUESTION_TIMEOUT_SECONDS,
            )
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise AIServiceUnavailable(
                    detail="invalid model question timeout"
                )
            return self._answer(
                question,
                owner_id=owner_id,
                asker=asker,
                policy_source=policy_source,
                app_facts=app_facts,
                today=today,
                deadline_monotonic=time.monotonic() + timeout,
            )
        except AccessDenied:
            return GroundedResponse(NEUTRAL_REPLY)
        except TamperDetected as error:
            return GroundedResponse(error.public_message)
        except (
            AIServiceUnavailable,
            AmbiguousName,
            PolicyFrozen,
            PolicySyntaxError,
        ):
            raise
        except Exception as error:
            raise AIServiceUnavailable(detail=type(error).__name__) from error

    def _answer(
        self,
        question: str,
        *,
        owner_id: str,
        asker: str,
        policy_source: str,
        app_facts: AppFacts,
        today: date,
        deadline_monotonic: float,
    ) -> GroundedResponse:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string.")
        if not isinstance(today, date) or isinstance(today, datetime):
            raise TypeError("today must be a date.")
        policy = parse(policy_source)
        records = self._diary_service.list_entries(owner_id)
        access_requests = tuple(
            AccessRequest(asker, record.entry.entry_id, level, today)
            for record in records
            for level in _LEVELS
        )
        entry_titles = tuple(
            record.entry.title
            for record in records
            if isinstance(record.entry, LetterEntry)
        )
        policy_titles = tuple(
            statement.title
            for statement in policy.statements
            if isinstance(statement, ReleaseLetter)
        )
        letter_titles = tuple(dict.fromkeys(entry_titles + policy_titles))
        status_requests = tuple(
            LetterStatusRequest(asker, title, today) for title in letter_titles
        )

        if access_requests or status_requests:
            batch = self._bridge.evaluate_many(
                policy,
                app_facts,
                access_requests=access_requests,
                letter_status_requests=status_requests,
            )
        else:
            batch = AccessBatchResult()
        permissions, statuses = self._map_batch_results(
            records, letter_titles, batch
        )
        release_dates = self._matching_release_dates(
            policy, asker, today, statuses
        )

        permitted_count = sum(
            permission is not None for permission in permissions.values()
        )
        verified_records: list[StoredEntry] = []
        tampered_ids: set[str] = set()
        for record in records:
            if permissions.get(record.entry.entry_id) is None:
                continue
            try:
                verify_entry(record)
            except TamperDetected:
                tampered_ids.add(record.entry.entry_id)
                continue
            verified_records.append(record)

        verified_permissions = dict(permissions)
        for entry_id in tampered_ids:
            verified_permissions[entry_id] = None

        if permitted_count and not verified_records:
            return GroundedResponse(TamperDetected().public_message)

        date_message = self._letter_date_message(
            question, statuses, release_dates
        )
        if date_message is not None:
            return GroundedResponse(date_message)
        if self._letter_request_without_access(question, statuses):
            return GroundedResponse(NEUTRAL_REPLY)
        if permitted_count == 0:
            return GroundedResponse(NEUTRAL_REPLY)

        usable_content = any(
            verified_permissions.get(record.entry.entry_id) == "verbatim"
            or (
                verified_permissions.get(record.entry.entry_id) == "summary"
                and self._summary_store.get(owner_id, record.entry.entry_id)
                is not None
            )
            for record in verified_records
        )
        has_existence_permission = any(
            level is not None for level in verified_permissions.values()
        )
        if not usable_content and not has_existence_permission:
            return GroundedResponse(NEUTRAL_REPLY)

        context = ToolContext(
            owner_id=owner_id,
            asker=asker,
            today=today,
            entries=records,
            permissions=verified_permissions,
            verified_entry_ids=frozenset(
                record.entry.entry_id for record in verified_records
            ),
            letter_statuses=statuses,
            release_dates=release_dates,
            summaries=self._summary_store,
        )
        return self._run_tool_loop(question, context, deadline_monotonic)

    def _map_batch_results(
        self,
        records: tuple[StoredEntry, ...],
        letter_titles: tuple[str, ...],
        batch: AccessBatchResult,
    ) -> tuple[dict[str, AccessLevel | None], dict[str, LetterStatus]]:
        """Map one ordered F5 batch to each entry's highest allowed level."""
        if not isinstance(batch, AccessBatchResult):
            raise AIServiceUnavailable(detail="malformed Prolog batch result")
        if len(batch.decisions) != len(records) * len(_LEVELS):
            raise AIServiceUnavailable(detail="malformed Prolog access result count")
        if len(batch.letter_statuses) != len(letter_titles):
            raise AIServiceUnavailable(detail="malformed Prolog status result count")
        if any(decision not in ("allow", "deny") for decision in batch.decisions):
            raise AIServiceUnavailable(detail="malformed Prolog access decision")
        if any(
            status not in ("released", "not_yet", "none")
            for status in batch.letter_statuses
        ):
            raise AIServiceUnavailable(detail="malformed Prolog letter status")

        permissions: dict[str, AccessLevel | None] = {}
        position = 0
        for record in records:
            decisions = batch.decisions[position : position + len(_LEVELS)]
            position += len(_LEVELS)
            highest = next(
                (
                    level
                    for level, decision in reversed(tuple(zip(_LEVELS, decisions)))
                    if decision == "allow"
                ),
                None,
            )
            permissions[record.entry.entry_id] = highest
        statuses = dict(zip(letter_titles, batch.letter_statuses))
        return permissions, statuses

    @staticmethod
    def _matching_release_dates(
        policy: Policy,
        asker: str,
        today: date,
        statuses: Mapping[str, LetterStatus],
    ) -> dict[str, date]:
        """Select a policy date only after Prolog reports a matching future rule."""
        rules: dict[str, list[date]] = {}
        for statement in policy.statements:
            if (
                isinstance(statement, ReleaseLetter)
                and statement.person.casefold() == asker.casefold()
            ):
                rules.setdefault(statement.title, []).append(statement.release_date)
        result: dict[str, date] = {}
        for title, status in statuses.items():
            if status != "not_yet":
                continue
            future_dates = tuple(
                release_date
                for release_date in rules.get(title, ())
                if release_date > today
            )
            if future_dates:
                result[title] = min(future_dates)
        return result

    @staticmethod
    def _letter_date_message(
        question: str,
        statuses: Mapping[str, LetterStatus],
        release_dates: Mapping[str, date],
    ) -> str | None:
        """Return a date message only for one explicitly asked-about release."""
        folded_question = question.casefold()
        matched_titles = tuple(
            title
            for title in statuses
            if title.casefold() in folded_question
        )
        if (
            len(matched_titles) != 1
            or statuses[matched_titles[0]] != "not_yet"
            or matched_titles[0] not in release_dates
        ):
            return None
        release_date = release_dates[matched_titles[0]]
        return LETTER_NOT_YET_MESSAGE.format(release_date=release_date.isoformat())

    @staticmethod
    def _letter_request_without_access(
        question: str,
        statuses: Mapping[str, LetterStatus],
    ) -> bool:
        """Keep unavailable letter titles out of model prompts and tool calls."""
        folded_question = question.casefold()
        matched_titles = tuple(
            title
            for title in statuses
            if title.casefold() in folded_question
        )
        if matched_titles:
            return any(statuses[title] != "released" for title in matched_titles)
        if '"' in folded_question:
            return True
        return False

    def _run_tool_loop(
        self,
        question: str,
        context: ToolContext,
        deadline_monotonic: float,
    ) -> GroundedResponse:
        messages = [PromptMessage("user", question)]
        presented_entries: dict[str, StoredEntry] = {}
        seen_signatures: set[tuple[str, str]] = set()
        steps = 0
        while steps < self._max_tool_steps:
            if time.monotonic() >= deadline_monotonic:
                raise AIServiceUnavailable(detail="model question deadline exceeded")
            prompt = ModelPrompt(
                SYSTEM_PROMPT,
                tuple(messages),
                TOOL_NAMES,
                deadline_monotonic,
            )
            try:
                response = self._model_client.complete(prompt)
            except AIServiceUnavailable:
                raise
            except Exception as error:
                raise AIServiceUnavailable(
                    detail=type(error).__name__
                ) from error
            if not isinstance(response, ModelResponse) or not isinstance(
                response.text, str
            ):
                raise AIServiceUnavailable(detail="malformed model response")
            if not isinstance(response.tool_calls, tuple):
                response = ModelResponse(response.text, (), ())

            if not response.tool_calls:
                return self._final_response(response, presented_entries)

            executed = False
            for call in response.tool_calls:
                if steps >= self._max_tool_steps:
                    raise AIServiceUnavailable(detail="tool-call step limit reached")
                steps += 1
                signature = (
                    call.name if isinstance(call, ToolCall) else "",
                    json.dumps(
                        call.arguments,
                        ensure_ascii=False,
                        sort_keys=True,
                        default=repr,
                    )
                    if isinstance(call, ToolCall)
                    else "",
                )
                if signature in seen_signatures:
                    raise AIServiceUnavailable(
                        detail="repeated model tool-call signature"
                    )
                seen_signatures.add(signature)
                result = self._execute_tool(call, context)
                if result is None:
                    continue
                executed = True
                if isinstance(result, GroundedResponse):
                    return result
                if isinstance(result, int):
                    name = self._tool_argument(call, "name")
                    return GroundedResponse(
                        f"Yes. {result} permitted record(s) mention {name}."
                    )
                if isinstance(result, tuple) and not result:
                    return GroundedResponse(NEUTRAL_REPLY)
                views = result if isinstance(result, tuple) else (result,)
                rendered: list[str] = []
                for view in views:
                    if not isinstance(view, EntryView):
                        continue
                    record = next(
                        (
                            item
                            for item in context.entries
                            if item.entry.entry_id == view.entry_id
                        ),
                        None,
                    )
                    if record is None:
                        continue
                    presented_entries[view.entry_id] = record
                    tag = (
                        "untrusted_entry"
                        if view.level == "verbatim"
                        else "derived_summary"
                    )
                    rendered.append(
                        render_untrusted_block(tag, view.entry_id, view.content)
                    )
                if not rendered:
                    return GroundedResponse(NEUTRAL_REPLY)
                messages.append(
                    PromptMessage(
                        "tool",
                        "\n".join(rendered)
                        + "\nNow summarize the permitted record blocks above "
                        "and return exact entry_id values in citation_ids.",
                    )
                )
            if not executed and response.text:
                return self._final_response(response, presented_entries)
            if not executed and not response.text and steps >= self._max_tool_steps:
                raise AIServiceUnavailable(detail="tool-call step limit reached")

        raise AIServiceUnavailable(detail="tool-call step limit reached")

    def _execute_tool(self, call: object, context: ToolContext) -> object | None:
        """Ignore malformed calls; execute only the four allowlisted tools."""
        if not isinstance(call, ToolCall) or not isinstance(call.name, str):
            return None
        if not isinstance(call.arguments, Mapping):
            return None
        arguments = call.arguments
        try:
            if call.name == "search_entries" and set(arguments) == {"query"}:
                query = arguments["query"]
                if not isinstance(query, str):
                    return None
                return search_entries(query, context)
            if call.name == "get_entry" and set(arguments) == {"entry_id"}:
                entry_id = arguments["entry_id"]
                if not isinstance(entry_id, str):
                    return None
                view = get_entry(entry_id, context)
                return view if view is not None else GroundedResponse(NEUTRAL_REPLY)
            if call.name == "count_mentions" and set(arguments) == {"name"}:
                name = arguments["name"]
                if not isinstance(name, str):
                    return None
                count = count_mentions(name, context)
                return (
                    GroundedResponse(NEUTRAL_REPLY)
                    if count == NEUTRAL_REPLY
                    else count
                )
            if call.name == "get_letter" and set(arguments) == {"title"}:
                title = arguments["title"]
                if not isinstance(title, str):
                    return None
                letter = get_letter(title, context)
                if letter.message is not None:
                    return GroundedResponse(letter.message)
                return letter.entry
        except AccessDenied:
            return GroundedResponse(NEUTRAL_REPLY)
        except TamperDetected as error:
            return GroundedResponse(error.public_message)
        return None

    @staticmethod
    def _tool_argument(call: ToolCall, name: str) -> str:
        if isinstance(call.arguments, Mapping):
            value = call.arguments.get(name)
            if isinstance(value, str):
                return value
        return ""

    @staticmethod
    def _final_response(
        response: ModelResponse,
        presented_entries: Mapping[str, StoredEntry],
    ) -> GroundedResponse:
        if not isinstance(response.citation_ids, tuple):
            raise AIServiceUnavailable(detail="malformed model citation list")
        grounded = attach_citations(
            response.text,
            response.citation_ids,
            presented_entries,
        )
        if not grounded.text.strip() or not grounded.citations:
            return GroundedResponse(NEUTRAL_REPLY)
        return grounded


__all__ = ["GroundedQAService"]
