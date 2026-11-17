# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting authentication tests over an object-oriented repository
from __future__ import annotations

import ast
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest

from app.ai.client import FakeModelClient, ModelResponse, ToolCall
from app.ai.summaries import InMemorySummaryStore
from app.domain.accounts import AccountRole, InMemoryUserRepository
from app.domain.diary import InMemoryEntryRepository
from app.errors import AuthenticationError, InvalidBeneficiaryError
from app.policy import PrologAccessBridge
from app.services.access_facts import build_app_facts
from app.services.auth_service import (
    LOGIN_DELAY_BASE_SECONDS,
    AuthService,
)
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService

ROOT = Path(__file__).parents[1]
SECRET = "s" * 32


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2040, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def make_service(clock: Clock | None = None) -> tuple[AuthService, InMemoryUserRepository, Clock]:
    actual_clock = clock or Clock()
    repository = InMemoryUserRepository()
    return AuthService(repository, clock=actual_clock, jwt_secret=SECRET), repository, actual_clock


def test_owner_registration_normalizes_identity_and_hashes_password():
    service, repository, _ = make_service()

    owner = service.register_owner("  Lola_Reyes ", "long-password-123")

    assert owner.username == "lola_reyes"
    assert owner.role is AccountRole.OWNER
    assert owner.password_hash != "long-password-123"
    assert repository.get_by_username("lola_reyes") == owner


@pytest.mark.parametrize(
    "password",
    ["short", "x" * 129, "lola"],
)
def test_password_rules_reject_short_long_or_username_equal(password):
    service, _, _ = make_service()

    with pytest.raises(ValueError):
        service.register_owner("lola", password)


def test_username_rules_and_normalized_uniqueness():
    service, _, _ = make_service()
    service.register_owner("Lola", "long-password-123")

    with pytest.raises(ValueError):
        service.register_owner(" lola ", "another-password-123")
    with pytest.raises(ValueError):
        service.register_owner("bad name", "another-password-123")


def test_beneficiary_username_differs_from_registered_person_id():
    service, _, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")
    code = service.create_invitation(
        owner.account_id, "Maria", clock.value + timedelta(hours=1)
    )

    beneficiary = service.register_beneficiary(
        owner.account_id, code, "adam_jr", "beneficiary-password-123"
    )

    assert beneficiary.person_id == "maria"
    assert service.registered_person_ids(owner.account_id) == ("lola", "maria")


def test_invitation_unknown_used_and_expired_fail_generically():
    service, _, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")
    code = service.create_invitation(
        owner.account_id, "maria", clock.value + timedelta(hours=1)
    )
    service.register_beneficiary(
        owner.account_id, code, "adam_jr", "beneficiary-password-123"
    )

    with pytest.raises(InvalidBeneficiaryError) as used:
        service.register_beneficiary(
            owner.account_id, code, "other_user", "other-password-123"
        )
    with pytest.raises(InvalidBeneficiaryError) as unknown:
        service.register_beneficiary(
            owner.account_id, "unknown-code", "other_user", "other-password-123"
        )

    assert str(used.value) == str(unknown.value)
    assert repr(used.value) == repr(unknown.value)

    expired = service.create_invitation(
        owner.account_id, "nora", clock.value + timedelta(hours=1)
    )
    clock.advance(3601)
    with pytest.raises(InvalidBeneficiaryError) as expired_error:
        service.register_beneficiary(
            owner.account_id, expired, "nora_user", "other-password-123"
        )
    assert str(expired_error.value) == str(unknown.value)


def test_reserved_or_invalid_person_and_duplicate_person_are_rejected():
    service, _, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")

    with pytest.raises(ValueError):
        service.create_invitation(
            owner.account_id, "May", clock.value + timedelta(hours=1)
        )
    with pytest.raises(ValueError):
        service.create_invitation(
            owner.account_id, "not-valid", clock.value + timedelta(hours=1)
        )

    code = service.create_invitation(
        owner.account_id, "maria", clock.value + timedelta(hours=1)
    )
    service.register_beneficiary(
        owner.account_id, code, "maria_user", "beneficiary-password-123"
    )
    with pytest.raises(ValueError):
        service.create_invitation(
            owner.account_id, "maria", clock.value + timedelta(hours=1)
        )


def test_invitation_cap_counts_only_outstanding_invitations():
    service, _, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")
    for index in range(10):
        service.create_invitation(
            owner.account_id,
            f"person_{index}",
            clock.value + timedelta(hours=1),
        )

    with pytest.raises(ValueError):
        service.create_invitation(
            owner.account_id, "eleven", clock.value + timedelta(hours=1)
        )


def test_login_issues_required_claims_and_reloads_account_from_subject():
    service, repository, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")

    token = service.login("LOLA", "owner-password-123")
    claims = jwt.decode(
        token, SECRET, algorithms=["HS256"], options={"verify_iat": False}
    )

    assert set(("sub", "role", "owner_id", "iat", "exp")) <= claims.keys()
    assert claims["sub"] == owner.account_id
    assert service.account_from_token(token) == owner
    repository._accounts.pop(owner.account_id)
    with pytest.raises(AuthenticationError):
        service.account_from_token(token)
    assert clock.value.tzinfo is not None


def test_jwt_secret_is_required_and_at_least_32_bytes():
    repository = InMemoryUserRepository()
    service = AuthService(repository, jwt_secret="short")

    with pytest.raises(AuthenticationError):
        service.register_owner("lola", "owner-password-123")
        service.login("lola", "owner-password-123")


def test_wrong_password_and_delayed_login_are_generic_with_escalating_clock(
    caplog: pytest.LogCaptureFixture,
):
    service, _, clock = make_service()
    service.register_owner("lola", "owner-password-123")

    with caplog.at_level(logging.INFO):
        with pytest.raises(AuthenticationError) as wrong:
            service.login("lola", "wrong-password-123")
        with pytest.raises(AuthenticationError) as delayed:
            service.login("lola", "owner-password-123")

    assert str(wrong.value) == str(delayed.value)
    assert repr(wrong.value) == repr(delayed.value)
    assert all("CANARY" not in record.getMessage() for record in caplog.records)
    clock.advance(LOGIN_DELAY_BASE_SECONDS * 2)
    assert service.login("lola", "owner-password-123")


def test_canary_password_never_appears_in_error_representations_or_logs(caplog):
    canary = "CANARY-PASSWORD-9a7f"
    service, _, _ = make_service()
    service.register_owner("lola", "owner-password-123")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(AuthenticationError) as error:
            service.login("lola", canary)

    assert canary not in str(error.value)
    assert canary not in repr(error.value)
    assert canary not in repr(error.value.args)
    assert all(canary not in record.getMessage() for record in caplog.records)


def test_maria_facts_are_authorized_by_real_prolog_bridge(swipl_executable):
    service, _, clock = make_service()
    owner = service.register_owner("lola", "owner-password-123")
    code = service.create_invitation(
        owner.account_id, "maria", clock.value + timedelta(hours=1)
    )
    service.register_beneficiary(
        owner.account_id, code, "adam_jr", "beneficiary-password-123"
    )
    diary = DiaryService(InMemoryEntryRepository())
    diary.add_diary_entry(
        owner.account_id,
        "family-1",
        "Family dinner #family",
        clock.value,
    )
    facts = build_app_facts(
        owner.account_id,
        diary.list_entries(owner.account_id),
        service.registered_person_ids(owner.account_id),
        death_triggered=True,
        policy_frozen=True,
    )
    model = FakeModelClient(
        (
            ModelResponse(
                "",
                tool_calls=(ToolCall("search_entries", {"query": "family"}),),
            ),
            ModelResponse("Family answer.", ("family-1",)),
        )
    )
    qa = GroundedQAService(
        diary,
        PrologAccessBridge(swipl_executable),
        model,
        InMemorySummaryStore(),
    )
    response = qa.answer(
        "What did he write about family?",
        owner_id=owner.account_id,
        asker="maria",
        policy_source='protocol maria:\n    may read verbatim of entries tagged "family"\n',
        app_facts=facts,
        today=clock.value.date(),
    )

    assert response.text == "Family answer."
    assert qa.answer(
        "What did he write about family?",
        owner_id=owner.account_id,
        asker="nora",
        policy_source='protocol maria:\n    may read verbatim of entries tagged "family"\n',
        app_facts=facts,
        today=clock.value.date(),
    ).text == "I couldn’t find any information in the records available to me."


def test_auth_modules_have_no_flask_or_database_imports():
    paths = [
        ROOT / "app" / "domain" / "accounts",
        ROOT / "app" / "services" / "auth_service.py",
    ]
    prohibited = {"flask", "sqlalchemy", "pymysql", "mysqlclient"}
    for path in paths:
        files = path.glob("*.py") if path.is_dir() else (path,)
        for source_path in files:
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            imports = (
                node.module
                if isinstance(node, ast.ImportFrom)
                else node.names[0].name
                if isinstance(node, ast.Import) and node.names
                else None
                for node in ast.walk(tree)
            )
            assert not any(
                module and any(
                    module == item or module.startswith(item + ".")
                    for item in prohibited
                )
                for module in imports
            )
