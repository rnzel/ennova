# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Scripting / isolated Prolog orchestration
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal, Sequence

from .ast_nodes import Policy
from .interpreter import interpret, quote_prolog_atom

AccessLevel = Literal["existence", "summary", "verbatim"]
AccessDecision = Literal["allow", "deny"]
EntryKind = Literal["diary", "letter"]

_LOGGER = logging.getLogger(__name__)
_RULES_PATH = Path(__file__).with_name("access_rules.pl")


@dataclass(frozen=True, slots=True)
class EntryFact:
    """Immutable app-provided entry identifier and Prolog entry type."""

    entry_id: str
    kind: EntryKind


@dataclass(frozen=True, slots=True)
class AppFacts:
    """Immutable app data loaded alongside the owner's interpreted policy."""

    registered_people: tuple[str, ...] = ()
    death_triggered: bool = False
    policy_frozen: bool = False
    entries: tuple[EntryFact, ...] = ()
    entry_mentions: tuple[tuple[str, str], ...] = ()
    entry_tags: tuple[tuple[str, str], ...] = ()
    letters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Require immutable tuple containers for app-provided facts."""
        for field_name in (
            "registered_people",
            "entries",
            "entry_mentions",
            "entry_tags",
            "letters",
        ):
            if not isinstance(getattr(self, field_name), tuple):
                raise TypeError(f"{field_name} must be a tuple.")
        if not isinstance(self.death_triggered, bool):
            raise TypeError("death_triggered must be a bool.")
        if not isinstance(self.policy_frozen, bool):
            raise TypeError("policy_frozen must be a bool.")


@dataclass(frozen=True, slots=True)
class AccessRequest:
    """One access check for a person, entry, level, and caller-supplied date."""

    person: str
    entry_id: str
    level: AccessLevel
    today: date


class PrologAccessBridge:
    """Run batched access queries in an isolated SWI-Prolog subprocess."""

    def __init__(
        self, executable: str | None = None, timeout_seconds: float = 3.0
    ) -> None:
        """Configure the SWI-Prolog executable and subprocess timeout."""
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        self._executable = executable or os.getenv("SWIPL_EXECUTABLE", "swipl")
        self._timeout_seconds = timeout_seconds

    def can_access(
        self, policy: Policy, app_facts: AppFacts, request: AccessRequest
    ) -> AccessDecision:
        """Return the Prolog decision for one access request, failing closed."""
        return self.can_access_many(policy, app_facts, (request,))[0]

    def can_access_many(
        self,
        policy: Policy,
        app_facts: AppFacts,
        requests: Sequence[AccessRequest],
    ) -> tuple[AccessDecision, ...]:
        """Evaluate a batch of access requests with one SWI-Prolog process."""
        try:
            request_items = tuple(requests)
        except TypeError:
            return ("deny",)
        if not request_items:
            return ()

        try:
            request_terms = tuple(
                self._serialize_access_request(request) for request in request_items
            )
            input_terms = self._build_input_terms(
                policy, app_facts, request_terms
            )
        except (AttributeError, TypeError, ValueError) as error:
            _LOGGER.warning("Unable to serialize Prolog access request: %s", type(error).__name__)
            return ("deny",) * len(request_items)
        return self._run(input_terms, len(request_items))

    def can_modify_policy(self, person: str, app_facts: AppFacts) -> bool:
        """Ask Prolog whether policy changes are allowed under the frozen-policy fact."""
        try:
            input_terms = self._build_input_terms(
                None,
                app_facts,
                (f"policy_request({quote_prolog_atom(person)})",),
            )
        except (AttributeError, TypeError, ValueError) as error:
            _LOGGER.warning("Unable to serialize policy-modification request: %s", type(error).__name__)
            return False
        return self._run(input_terms, 1)[0] == "allow"

    def _build_input_terms(
        self,
        policy: Policy | None,
        app_facts: AppFacts,
        request_terms: tuple[str, ...],
    ) -> str:
        """Serialize policy facts, app facts, and a final request batch as Prolog data."""
        if not isinstance(app_facts, AppFacts):
            raise TypeError("app_facts must be AppFacts.")

        terms = list(interpret(policy)) if policy is not None else []
        terms.extend(self._serialize_app_facts(app_facts))
        terms.append(f"request_batch([{','.join(request_terms)}]).")
        return "\n".join(terms) + "\n"

    @staticmethod
    def _serialize_app_facts(app_facts: AppFacts) -> tuple[str, ...]:
        """Encode each app-provided fact using the shared F4 Prolog atom escaper."""
        terms: list[str] = []
        for person in app_facts.registered_people:
            terms.append(f"registered({quote_prolog_atom(person.casefold())}).")
        if app_facts.death_triggered:
            terms.append("death_triggered.")
        if app_facts.policy_frozen:
            terms.append("policy_frozen.")

        for entry in app_facts.entries:
            if not isinstance(entry, EntryFact) or entry.kind not in ("diary", "letter"):
                raise ValueError("entries must contain valid EntryFact values.")
            terms.append(
                f"entry({quote_prolog_atom(entry.entry_id)}, {entry.kind})."
            )
        for entry_id, name in app_facts.entry_mentions:
            terms.append(
                "entry_mentions("
                f"{quote_prolog_atom(entry_id)}, {quote_prolog_atom(name.casefold())})."
            )
        for entry_id, tag in app_facts.entry_tags:
            terms.append(
                f"entry_tag({quote_prolog_atom(entry_id)}, "
                f"{quote_prolog_atom(tag.casefold())})."
            )
        for entry_id, title in app_facts.letters:
            terms.append(
                f"letter({quote_prolog_atom(entry_id)}, {quote_prolog_atom(title)})."
            )
        return tuple(terms)

    @staticmethod
    def _serialize_access_request(request: AccessRequest) -> str:
        """Encode one query as a data term; no input is used as a Prolog goal."""
        if not isinstance(request, AccessRequest):
            raise TypeError("requests must contain AccessRequest values.")
        if not isinstance(request.today, date) or isinstance(request.today, datetime):
            raise TypeError("request.today must be a date.")
        return (
            "access_request("
            f"{quote_prolog_atom(request.person.casefold())}, "
            f"{quote_prolog_atom(request.entry_id)}, "
            f"{quote_prolog_atom(str(request.level).casefold())}, "
            f"date({request.today.year},{request.today.month},{request.today.day}))"
        )

    def _run(self, input_terms: str, expected_results: int) -> tuple[AccessDecision, ...]:
        """Run one data-only Prolog request and validate its exact output shape."""
        fallback: tuple[AccessDecision, ...] = ("deny",) * expected_results
        command = [
            self._executable,
            "-f",
            "none",
            "-q",
            "-s",
            str(_RULES_PATH),
            "-g",
            "run_from_stdin",
            "-t",
            "halt",
        ]
        try:
            result = subprocess.run(
                command,
                input=input_terms,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout_seconds,
                shell=False,
                check=False,
            )
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            _LOGGER.warning("SWI-Prolog invocation failed: %s", type(error).__name__)
            return fallback

        if not isinstance(result, subprocess.CompletedProcess):
            _LOGGER.warning("SWI-Prolog returned an invalid process result.")
            return fallback
        if result.returncode != 0:
            _LOGGER.warning("SWI-Prolog exited with status %s.", result.returncode)
            return fallback
        if not isinstance(result.stdout, str) or not isinstance(result.stderr, str):
            _LOGGER.warning("SWI-Prolog returned malformed process output.")
            return fallback
        if result.stderr.strip():
            _LOGGER.warning("SWI-Prolog emitted diagnostics; denying the request.")
            return fallback
        decisions = result.stdout.splitlines()
        if len(decisions) != expected_results or any(
            decision not in ("allow", "deny") for decision in decisions
        ):
            _LOGGER.warning("SWI-Prolog returned malformed decision output.")
            return fallback
        typed_decisions: list[AccessDecision] = []
        for decision in decisions:
            typed_decisions.append("allow" if decision == "allow" else "deny")
        return tuple(typed_decisions)


__all__ = [
    "AccessDecision",
    "AccessLevel",
    "AccessRequest",
    "AppFacts",
    "EntryFact",
    "PrologAccessBridge",
]
