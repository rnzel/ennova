# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP security boundary tests
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app import create_app
from app.ai.client import FakeModelClient
from app.ai.prompts import NEUTRAL_REPLY
from app.ai.summaries import FakeSummarizer

pytestmark = pytest.mark.filterwarnings(
    "ignore:Using the in-memory storage for tracking rate limits"
)


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2040, 4, 30, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value


def build_app(model_client=None, swipl_executable=None):
    clock = Clock()
    overrides = {
        "TESTING": True,
        "JWT_SECRET_KEY": "j" * 32,
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URI": "memory://",
        "APP_TIMEZONE": "UTC",
    }
    if swipl_executable is not None:
        overrides["SWIPL_EXECUTABLE"] = swipl_executable
    app = create_app(
        clock=clock,
        model_client=model_client,
        summarizer=FakeSummarizer(),
        config_overrides=overrides,
    )
    return app


def register_owner(client, username: str = "lola") -> str:
    password = f"{username}-owner-password"
    assert client.post(
        "/auth/register-owner",
        json={"username": username, "password": password},
    ).status_code == 201
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def issue_invitation(client, token: str, person_id: str) -> str:
    response = client.post(
        "/invitations",
        headers=auth(token),
        json={
            "person_id": person_id,
            "expires_at": "2040-05-02T00:00:00+00:00",
        },
    )
    assert response.status_code == 201
    return response.get_json()["invitation_code"]


def redeem(client, code: str, username: str = "maria_user") -> str:
    response = client.post(
        "/auth/register-beneficiary",
        json={
            "invitation_code": code,
            "username": username,
            "password": f"{username}-beneficiary-password",
        },
    )
    assert response.status_code == 201
    return response.get_json()["account_id"]


def trigger(client, token: str) -> None:
    response = client.post(
        "/death-trigger",
        headers=auth(token),
        json={
            "password": "lola-owner-password",
            "confirmation": "I CONFIRM DEATH TRIGGER",
        },
    )
    assert response.status_code == 200


def activate_family_policy(client, token: str) -> None:
    response = client.put(
        "/policy",
        headers=auth(token),
        json={
            "source": (
                "protocol maria:\n"
                '    may read summary of entries tagged "family"\n'
            )
        },
    )
    assert response.status_code == 201


def test_maria_is_neutral_before_death_trigger(swipl_executable):
    app = build_app(FakeModelClient(()), swipl_executable)
    client = app.test_client()
    owner_token = register_owner(client)
    code = issue_invitation(client, owner_token, "maria")
    maria_account_id = redeem(client, code)
    activate_family_policy(client, owner_token)
    maria = app.extensions["auth_service"]._repository.get_by_account_id(
        maria_account_id
    )
    maria_token = app.extensions["auth_service"].login(
        maria.username, "maria_user-beneficiary-password"
    )

    response = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": "What did he write about family?"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"answer": NEUTRAL_REPLY, "citations": []}


def test_policy_is_refused_after_trigger_and_previous_version_remains():
    app = build_app()
    client = app.test_client()
    owner_token = register_owner(client)
    activate_family_policy(client, owner_token)
    trigger(client, owner_token)

    response = client.put(
        "/policy",
        headers=auth(owner_token),
        json={"source": "protocol maria:\n    may see existence of entries\n"},
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "policy_frozen"
    assert app.extensions["api_state"].active_policy(
        app.extensions["auth_service"].account_from_token(owner_token).owner_id
    ).source.startswith("protocol maria:")
    assert "may read summary" in app.extensions["api_state"].active_policy(
        app.extensions["auth_service"].account_from_token(owner_token).owner_id
    ).source


def test_writes_are_refused_after_trigger_but_existing_invitation_redeems():
    app = build_app()
    client = app.test_client()
    owner_token = register_owner(client)
    code = issue_invitation(client, owner_token, "maria")
    trigger(client, owner_token)

    entry = client.post(
        "/entries",
        headers=auth(owner_token),
        json={"entry_id": "after-trigger", "kind": "diary", "content": "text"},
    )
    invitation = client.post(
        "/invitations",
        headers=auth(owner_token),
        json={
            "person_id": "nora",
            "expires_at": "2040-05-02T00:00:00+00:00",
        },
    )

    assert entry.status_code == 403
    assert invitation.status_code == 403
    assert redeem(client, code) is not None


def test_identity_fields_in_registration_body_are_ignored():
    app = build_app()
    client = app.test_client()
    owner_token = register_owner(client)
    owner = app.extensions["auth_service"].account_from_token(owner_token)
    code = issue_invitation(client, owner_token, "maria")

    response = client.post(
        "/auth/register-beneficiary",
        json={
            "invitation_code": code,
            "username": "adam_jr",
            "password": "adam_jr-beneficiary-password",
            "owner_id": "attacker-owner",
            "role": "owner",
        },
    )

    body = response.get_json()
    assert response.status_code == 201
    assert body["role"] == "beneficiary"
    assert body["owner_id"] == owner.account_id
    assert body["person_id"] == "maria"


def test_unknown_exception_canary_is_not_public_or_audited(monkeypatch):
    app = create_app(
        clock=Clock(),
        model_client=FakeModelClient(()),
        summarizer=FakeSummarizer(),
        config_overrides={
            "TESTING": True,
            "JWT_SECRET_KEY": "j" * 32,
            "RATELIMIT_ENABLED": True,
            "RATELIMIT_STORAGE_URI": "memory://",
            "APP_TIMEZONE": "UTC",
        },
    )
    client = app.test_client()
    owner_token = register_owner(client)
    code = issue_invitation(client, owner_token, "maria")
    maria_account_id = redeem(client, code)
    maria = app.extensions["auth_service"]._repository.get_by_account_id(
        maria_account_id
    )
    activate_family_policy(client, owner_token)
    trigger(client, owner_token)
    maria_token = app.extensions["auth_service"].login(
        maria.username, "maria_user-beneficiary-password"
    )
    canary = "UNKNOWN-EXCEPTION-CANARY-91"

    def fail(_owner_id):
        raise RuntimeError(canary)

    monkeypatch.setitem(app.extensions, "facts_builder", fail)
    response = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": "family"},
    )

    assert response.status_code == 500
    assert canary not in response.get_data(as_text=True)
    assert all(canary not in value for value in response.headers.values())
    assert all(canary not in repr(record) for record in app.extensions["api_state"].audits())


def test_audit_records_exclude_entry_and_question_text():
    app = build_app()
    client = app.test_client()
    owner_token = register_owner(client)
    entry_text = "ENTRY-AUDIT-CANARY-18"
    question_text = "QUESTION-AUDIT-CANARY-27"
    assert client.post(
        "/entries",
        headers=auth(owner_token),
        json={
            "entry_id": "audit-entry",
            "kind": "diary",
            "content": entry_text,
        },
    ).status_code == 201
    assert client.post(
        "/ask",
        headers=auth(owner_token),
        json={"question": question_text},
    ).status_code == 200
    trigger(client, owner_token)

    audit_text = repr(app.extensions["api_state"].audits())
    assert entry_text not in audit_text
    assert question_text not in audit_text


def test_oversized_body_and_non_json_are_rejected():
    app = build_app()
    client = app.test_client()

    oversized = client.post(
        "/auth/register-owner",
        data=("x" * (1_048_576 + 1)).encode(),
        content_type="application/json",
    )
    non_json = client.post(
        "/auth/register-owner",
        data="username=lola",
        content_type="text/plain",
    )

    assert oversized.status_code == 413
    assert non_json.status_code == 400


def test_denied_and_no_record_ask_responses_are_identical(swipl_executable):
    app = build_app(FakeModelClient(()), swipl_executable)
    client = app.test_client()
    owner_token = register_owner(client)
    maria_code = issue_invitation(client, owner_token, "maria")
    nora_code = issue_invitation(client, owner_token, "nora")
    redeem(client, maria_code, "maria_user")
    redeem(client, nora_code, "nora_user")
    activate_family_policy(client, owner_token)
    trigger(client, owner_token)
    maria_token = app.extensions["auth_service"].login(
        "maria_user", "maria_user-beneficiary-password"
    )
    nora_token = app.extensions["auth_service"].login(
        "nora_user", "nora_user-beneficiary-password"
    )

    no_record = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": "What did he write about family?"},
    )
    denied = client.post(
        "/ask",
        headers=auth(nora_token),
        json={"question": "What did he write about family?"},
    )

    assert no_record.status_code == denied.status_code == 200
    assert no_record.get_data() == denied.get_data()
    for header in ("Cache-Control", "X-Content-Type-Options"):
        assert no_record.headers[header] == denied.headers[header]


def test_unredeemed_person_is_denied_through_api(swipl_executable):
    app = build_app(FakeModelClient(()), swipl_executable)
    client = app.test_client()
    owner_token = register_owner(client)
    nora_code = issue_invitation(client, owner_token, "nora")
    issue_invitation(client, owner_token, "maria")
    redeem(client, nora_code, "nora_user")
    activate_family_policy(client, owner_token)
    client.post(
        "/entries",
        headers=auth(owner_token),
        json={
            "entry_id": "family-entry",
            "kind": "diary",
            "content": "Family dinner #family",
        },
    )
    trigger(client, owner_token)
    nora_token = app.extensions["auth_service"].login(
        "nora_user", "nora_user-beneficiary-password"
    )

    response = client.post(
        "/ask",
        headers=auth(nora_token),
        json={"question": "What did he write about family?"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"answer": NEUTRAL_REPLY, "citations": []}


def test_ask_limit_is_keyed_per_account():
    app = build_app()
    limiter = app.extensions["limiter"]
    limiter.reset()
    client = app.test_client()
    first = register_owner(client, "lola")
    second = register_owner(client, "maria")

    responses = [
        client.post("/ask", headers=auth(first), json={"question": "x"})
        for _ in range(21)
    ]

    assert responses[-1].status_code == 429
    assert client.post(
        "/ask", headers=auth(second), json={"question": "x"}
    ).status_code == 200


def test_death_trigger_limit_is_keyed_per_account():
    app = build_app()
    limiter = app.extensions["limiter"]
    limiter.reset()
    client = app.test_client()
    first = register_owner(client, "lola")
    second = register_owner(client, "maria")

    def request(token, password):
        return client.post(
            "/death-trigger",
            headers=auth(token),
            json={
                "password": password,
                "confirmation": "I CONFIRM DEATH TRIGGER",
            },
        )

    first_responses = [
        request(first, "lola-owner-password") for _ in range(6)
    ]

    assert first_responses[-1].status_code == 429
    assert request(second, "maria-owner-password").status_code == 200
