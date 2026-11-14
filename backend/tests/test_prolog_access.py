# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Logic programming / Prolog access-rule tests
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from app.policy import (
    AccessRequest,
    AppFacts,
    EntryFact,
    PrologAccessBridge,
    interpret,
    parse,
)

ROOT = Path(__file__).parents[2]
RULES_PATH = ROOT / "backend" / "app" / "policy" / "access_rules.pl"
ACCESS_TABLE_PATH = ROOT / "docs" / "access-test-table.md"
MARIA_SAMPLE_PATH = ROOT / "docs" / "grammar" / "sample_maria.policy"

POLICY_SOURCES = {
    "archive_verbatim": (
        "protocol maria:\n"
        '    may read verbatim of entries tagged "Archive"\n'
    ),
    "guest_grant": (
        "protocol guest:\n"
        '    may read verbatim of entries tagged "Family"\n'
    ),
    "letters_grant": (
        "protocol maria:\n"
        '    may read verbatim of entries tagged "Letters"\n'
    ),
    "letter_deny": (
        "protocol maria:\n"
        '    may not see existence of entries tagged "Letters"\n'
        'release letter "To my daughter" to maria when date >= 2040-05-01\n'
    ),
    "private_deny": (
        "protocol maria:\n"
        '    may read verbatim of entries tagged "Private"\n'
        '    may not read summary of entries tagged "Private"\n'
        "    may not see existence of entries mentioning secret\n"
    ),
}

ACTIVE_FACTS = AppFacts(
    registered_people=("Maria", "Nora"),
    death_triggered=True,
    entries=(
        EntryFact("e_maria", "diary"),
        EntryFact("e_family", "diary"),
        EntryFact("e_business", "diary"),
        EntryFact("e_private", "diary"),
        EntryFact("e_secret", "diary"),
        EntryFact("e_archive", "diary"),
        EntryFact("e_letter", "letter"),
    ),
    entry_mentions=(("e_maria", "Maria"), ("e_secret", "Secret")),
    entry_tags=(
        ("e_family", "Family"),
        ("e_business", "Business"),
        ("e_private", "Private"),
        ("e_archive", "Archive"),
        ("e_letter", "Letters"),
    ),
    letters=(("e_letter", "To my daughter"),),
)


@pytest.fixture(scope="session")
def swipl_executable() -> str:
    """Find SWI-Prolog or fail the test suite because F5 requires it."""
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
    pytest.fail("SWI-Prolog is required for F5 tests but was not found.")


@pytest.fixture
def bridge(swipl_executable: str) -> PrologAccessBridge:
    """Create a bridge pointed at the required SWI-Prolog executable."""
    return PrologAccessBridge(swipl_executable, timeout_seconds=5.0)


def _read_access_table() -> tuple[dict[str, str], ...]:
    """Read executable case rows from the documented Markdown table."""
    rows: list[dict[str, str]] = []
    lines = ACCESS_TABLE_PATH.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(dict(zip(header, cells)))
    return tuple(rows)


def _policy_source(policy_key: str) -> str:
    """Resolve a table policy key to its handout sample or small test program."""
    if policy_key == "maria_sample":
        return MARIA_SAMPLE_PATH.read_text(encoding="utf-8")
    return POLICY_SOURCES[policy_key]


def _app_facts(context: str) -> AppFacts:
    """Build the app facts named by a row in the access-test table."""
    if context == "active":
        return ACTIVE_FACTS
    if context == "before_death":
        return replace(ACTIVE_FACTS, death_triggered=False)
    raise ValueError(f"Unknown test context: {context}")


def _requests(rows: tuple[dict[str, str], ...]) -> tuple[AccessRequest, ...]:
    """Translate table rows into immutable bridge requests."""
    return tuple(
        AccessRequest(
            person=row["Asker"],
            entry_id=row["Entry ID"],
            level=row["Level"],
            today=date.fromisoformat(row["Today"]),
        )
        for row in rows
    )


def test_maria_scenario_parses_interprets_loads_and_queries_in_one_batch(
    bridge: PrologAccessBridge,
):
    rows = tuple(
        row for row in _read_access_table() if row["Scenario"] == "maria_acceptance"
    )
    assert len(rows) == 6
    policy = parse(_policy_source("maria_sample"))
    assert interpret(policy) == (
        "grant(maria, existence, mentioning(maria)).",
        "grant(maria, summary, tagged(family)).",
        "release(maria, 'To my daughter', date(2040,5,1)).",
        "custody_rule(adam_jr, trustee_unavailable, 90).",
        "default_mode(light_fix).",
    )

    decisions = bridge.can_access_many(policy, _app_facts("active"), _requests(rows))

    assert decisions == tuple(row["Expected"] for row in rows)


def test_access_rules_are_driven_by_the_documented_table(bridge: PrologAccessBridge):
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in _read_access_table():
        if row["Scenario"] == "maria_acceptance":
            continue
        grouped.setdefault((row["Policy"], row["Context"]), []).append(row)

    for (policy_key, context), rows in grouped.items():
        decisions = bridge.can_access_many(
            parse(_policy_source(policy_key)),
            _app_facts(context),
            _requests(tuple(rows)),
        )
        assert decisions == tuple(row["Expected"] for row in rows), policy_key


def test_policy_modification_fails_only_when_frozen(bridge: PrologAccessBridge):
    policy = parse("")

    assert bridge.can_modify_policy("owner", ACTIVE_FACTS) is True
    assert bridge.can_modify_policy(
        "owner", replace(ACTIVE_FACTS, policy_frozen=True)
    ) is False
    assert interpret(policy) == ()


def test_policy_modification_bridge_fails_closed_on_process_failure(
    bridge: PrologAccessBridge, monkeypatch: pytest.MonkeyPatch
):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired("swipl", 1)

    monkeypatch.setattr("app.policy.access_bridge.subprocess.run", fake_run)

    assert bridge.can_modify_policy("owner", ACTIVE_FACTS) is False


@pytest.mark.parametrize(
    "stdout",
    ["", "allow\n", "allow\ndeny\nextra\n", "PERMIT\n", " allow \n"],
)
def test_bridge_returns_deny_for_malformed_batch_output(
    bridge: PrologAccessBridge, monkeypatch: pytest.MonkeyPatch, stdout: str
):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout, "")

    monkeypatch.setattr("app.policy.access_bridge.subprocess.run", fake_run)
    requests = (
        AccessRequest("maria", "e1", "summary", date(2040, 5, 1)),
        AccessRequest("maria", "e2", "summary", date(2040, 5, 1)),
    )

    assert bridge.can_access_many(parse(""), ACTIVE_FACTS, requests) == (
        "deny",
        "deny",
    )


@pytest.mark.parametrize(
    "failure",
    [
        OSError("missing executable"),
        subprocess.TimeoutExpired("swipl", 1),
        subprocess.SubprocessError("process failure"),
    ],
)
def test_bridge_returns_deny_for_process_failures(
    bridge: PrologAccessBridge,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
):
    def fake_run(*args, **kwargs):
        raise failure

    monkeypatch.setattr("app.policy.access_bridge.subprocess.run", fake_run)
    request = AccessRequest("maria", "e1", "summary", date(2040, 5, 1))

    assert bridge.can_access(parse(""), ACTIVE_FACTS, request) == "deny"


def test_bridge_returns_deny_for_nonzero_exit_and_uses_safe_batch_cli(
    bridge: PrologAccessBridge, monkeypatch: pytest.MonkeyPatch
):
    captured = {}

    def fake_run(*args, **kwargs):
        captured["command"] = args[0]
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args[0], 1, "allow\n", "diagnostic")

    monkeypatch.setattr("app.policy.access_bridge.subprocess.run", fake_run)
    requests = (
        AccessRequest("maria", "e1", "summary", date(2040, 5, 1)),
        AccessRequest("maria", "e2", "summary", date(2040, 5, 1)),
    )

    assert bridge.can_access_many(parse(""), ACTIVE_FACTS, requests) == (
        "deny",
        "deny",
    )
    command = captured["command"]
    assert command[1:4] == ["-f", "none", "-q"]
    assert command[command.index("-g") + 1] == "run_from_stdin"
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["input"].count("access_request(") == 2
    assert "registered('maria')." in captured["kwargs"]["input"]
    assert "entry_tag('e_family', 'family')." in captured["kwargs"]["input"]


def test_bridge_evaluates_a_batch_in_exactly_one_subprocess(
    bridge: PrologAccessBridge, monkeypatch: pytest.MonkeyPatch
):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, "allow\ndeny\n", "")

    monkeypatch.setattr("app.policy.access_bridge.subprocess.run", fake_run)
    requests = (
        AccessRequest("maria", "e1", "summary", date(2040, 5, 1)),
        AccessRequest("maria", "e2", "summary", date(2040, 5, 1)),
    )

    assert bridge.can_access_many(parse(""), ACTIVE_FACTS, requests) == (
        "allow",
        "deny",
    )
    assert len(calls) == 1


def test_query_values_are_escaped_as_data_not_interpreted_as_prolog(
    bridge: PrologAccessBridge,
):
    request = AccessRequest(
        "maria'), halt. %",
        "e1'), unlisted_fact(secret), %",
        "summary",
        date(2040, 5, 1),
    )

    assert bridge.can_access(parse(""), ACTIVE_FACTS, request) == "deny"


def test_bridge_transports_unicode_policy_atoms_as_utf8(bridge: PrologAccessBridge):
    policy = parse(
        'release letter "Letter ☃" to maria when date >= 2040-05-01\n'
    )
    facts = AppFacts(
        registered_people=("maria",),
        death_triggered=True,
        entries=(EntryFact("letter_snowman", "letter"),),
        letters=(("letter_snowman", "Letter ☃"),),
    )

    assert bridge.can_access(
        policy,
        facts,
        AccessRequest("maria", "letter_snowman", "verbatim", date(2040, 5, 1)),
    ) == "allow"


def test_untrusted_directive_is_read_as_data_and_denied(swipl_executable: str):
    request = "request_batch([access_request('maria','e1',summary,date(2040,5,1))])."
    result = subprocess.run(
        [
            swipl_executable,
            "-f",
            "none",
            "-q",
            "-s",
            str(RULES_PATH),
            "-g",
            "run_from_stdin",
            "-t",
            "halt",
        ],
        input=":- halt.\n" + request + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
        shell=False,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["deny"]


def test_unlisted_input_predicate_is_whitelisted_out_and_denied(swipl_executable: str):
    request = "request_batch([access_request('maria','e1',summary,date(2040,5,1))])."
    result = subprocess.run(
        [
            swipl_executable,
            "-f",
            "none",
            "-q",
            "-s",
            str(RULES_PATH),
            "-g",
            "run_from_stdin",
            "-t",
            "halt",
        ],
        input="unlisted_fact(secret).\n" + request + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
        shell=False,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["deny"]
