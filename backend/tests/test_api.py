# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP API tests over in-memory services
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app import create_app
from app.ai.client import FakeModelClient, ModelResponse, ToolCall
from app.ai.prompts import NEUTRAL_REPLY
from app.ai.summaries import FakeSummarizer
from app.errors import AIServiceUnavailable


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2040, 4, 30, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs) -> None:
        self.value += timedelta(**kwargs)


def build_app(
    model_client=None,
    summarizer=None,
    clock=None,
    swipl_executable=None,
):
    actual_clock = clock or Clock()
    config_overrides = {
        "TESTING": True,
        "JWT_SECRET_KEY": "j" * 32,
        "RATELIMIT_ENABLED": True,
        "APP_TIMEZONE": "Asia/Manila",
    }
    if swipl_executable is not None:
        config_overrides["SWIPL_EXECUTABLE"] = swipl_executable
    return create_app(
        clock=actual_clock,
        model_client=model_client,
        summarizer=summarizer or FakeSummarizer(),
        config_overrides=config_overrides,
    ), actual_clock


def register_owner(client):
    response = client.post(
        "/auth/register-owner",
        json={"username": "lola", "password": "owner-password-123"},
    )
    assert response.status_code == 201
    login = client.post(
        "/auth/login",
        json={"username": "lola", "password": "owner-password-123"},
    )
    return login.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_factory_starts_without_provider_and_ask_is_neutral():
    app, _ = build_app()
    client = app.test_client()
    token = register_owner(client)

    assert client.post(
        "/ask", headers=auth(token), json={"question": "Anything?"}
    ).get_json()["answer"] == NEUTRAL_REPLY


def test_owner_entry_is_saved_and_summary_failure_does_not_change_response():
    class FailingSummarizer:
        def summarize(self, record):
            raise AIServiceUnavailable({"reason": "summary_failed"})

    app, _ = build_app(summarizer=FailingSummarizer())
    client = app.test_client()
    token = register_owner(client)
    response = client.post(
        "/entries",
        headers=auth(token),
        json={
            "entry_id": "family-1",
            "kind": "diary",
            "content": "Family dinner #family",
        },
    )

    assert response.status_code == 201
    assert client.get("/entries", headers=auth(token)).get_json()["entries"]
    assert "summary" not in response.get_json()


def test_bearer_auth_has_same_body_shape_for_401_and_403():
    app, _ = build_app()
    client = app.test_client()

    missing = client.get("/entries")
    owner_token = register_owner(client)
    beneficiary_token = None
    invitation = client.post(
        "/invitations",
        headers=auth(owner_token),
        json={
            "person_id": "maria",
            "expires_at": "2040-05-01T00:00:00+00:00",
        },
    ).get_json()["invitation_code"]
    beneficiary = client.post(
        "/auth/register-beneficiary",
        json={
            "invitation_code": invitation,
            "username": "adam_jr",
            "password": "beneficiary-password-123",
        },
    )
    assert beneficiary.status_code == 201
    beneficiary_token = client.post(
        "/auth/login",
        json={"username": "adam_jr", "password": "beneficiary-password-123"},
    ).get_json()["access_token"]
    forbidden = client.post(
        "/entries",
        headers=auth(beneficiary_token),
        json={"entry_id": "x", "kind": "diary", "content": "x"},
    )

    assert set(missing.get_json()) == set(forbidden.get_json())
    assert missing.status_code == 401
    assert forbidden.status_code == 403


def test_policy_syntax_error_is_located_and_rejected():
    app, _ = build_app()
    client = app.test_client()
    token = register_owner(client)

    response = client.put(
        "/policy",
        headers=auth(token),
        json={"source": "protocol maria:\n    may read summary\n"},
    )

    assert response.status_code == 400
    assert {"line", "column", "message", "code"} <= response.get_json().keys()
    assert app.extensions["api_state"].active_policy(
        app.extensions["auth_service"].account_from_token(token).owner_id
    ) is None


def test_maria_http_scenario_release_boundary_and_nora_neutral(swipl_executable):
    model = FakeModelClient(
        (
            ModelResponse(
                "",
                tool_calls=(ToolCall("search_entries", {"query": "family"}),),
            ),
            ModelResponse("Family answer.", ("family-1",)),
            ModelResponse(
                "",
                tool_calls=(
                    ToolCall("get_letter", {"title": "To my daughter"}),
                ),
            ),
            ModelResponse("A message for Maria.", ("letter-1",)),
        )
    )
    clock = Clock()
    app, _ = build_app(
        model_client=model,
        clock=clock,
        swipl_executable=swipl_executable,
    )
    client = app.test_client()
    owner_token = register_owner(client)
    client.post(
        "/entries",
        headers=auth(owner_token),
        json={
            "entry_id": "family-1",
            "kind": "diary",
            "content": "Family dinner #family",
        },
    )
    client.post(
        "/entries",
        headers=auth(owner_token),
        json={
            "entry_id": "letter-1",
            "kind": "letter",
            "content": "A message for Maria.",
            "title": "To my daughter",
            "recipient": "maria",
        },
    )
    policy = (
        "protocol maria:\n"
        '    may read summary of entries tagged "family"\n'
        'release letter "To my daughter" to maria when date >= 2040-05-01\n'
    )
    assert client.put(
        "/policy", headers=auth(owner_token), json={"source": policy}
    ).status_code == 201
    code = client.post(
        "/invitations",
        headers=auth(owner_token),
        json={
            "person_id": "maria",
            "expires_at": "2040-05-02T00:00:00+00:00",
        },
    ).get_json()["invitation_code"]
    client.post(
        "/auth/register-beneficiary",
        json={
            "invitation_code": code,
            "username": "adam_jr",
            "password": "beneficiary-password-123",
        },
    )
    nora_code = client.post(
        "/invitations",
        headers=auth(owner_token),
        json={
            "person_id": "nora",
            "expires_at": "2040-05-02T00:00:00+00:00",
        },
    ).get_json()["invitation_code"]
    maria_token = client.post(
        "/auth/login",
        json={"username": "adam_jr", "password": "beneficiary-password-123"},
    ).get_json()["access_token"]
    assert client.post(
        "/death-trigger",
        headers=auth(owner_token),
        json={
            "password": "owner-password-123",
            "confirmation": "I CONFIRM DEATH TRIGGER",
        },
    ).status_code == 200
    summary = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": "What did he write about family?"},
    )
    assert summary.status_code == 200
    assert summary.get_json()["citations"] == [
        {"entry_id": "family-1", "date": "2040-04-30"}
    ]
    before = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": 'Show me "To my daughter".'},
    )
    assert before.get_json()["answer"] == (
        "That letter will be available on 2040-05-01."
    )
    clock.advance(days=1)
    maria_token = client.post(
        "/auth/login",
        json={"username": "adam_jr", "password": "beneficiary-password-123"},
    ).get_json()["access_token"]
    after = client.post(
        "/ask",
        headers=auth(maria_token),
        json={"question": 'Show me "To my daughter".'},
    )
    after_body = after.get_json()
    assert after.status_code == 200 and "A message for Maria." in after_body.get(
        "answer", ""
    ), (after.status_code, after_body)
    nora_registration = client.post(
        "/auth/register-beneficiary",
        json={
            "invitation_code": nora_code,
            "username": "nora_user",
            "password": "nora-password-123",
        },
    )
    assert nora_registration.status_code == 201
    nora_token = client.post(
        "/auth/login",
        json={"username": "nora_user", "password": "nora-password-123"},
    ).get_json()["access_token"]
    nora = client.post(
        "/ask",
        headers=auth(nora_token),
        json={"question": "What did he write about family?"},
    )
    assert nora.status_code == 200
    assert nora.get_json() == {"answer": NEUTRAL_REPLY, "citations": []}
    owner_token = client.post(
        "/auth/login",
        json={"username": "lola", "password": "owner-password-123"},
    ).get_json()["access_token"]
    assert client.post(
        "/death-trigger",
        headers=auth(owner_token),
        json={
            "password": "owner-password-123",
            "confirmation": "I CONFIRM DEATH TRIGGER",
        },
    ).status_code == 200
    assert client.post(
        "/invitations",
        headers=auth(owner_token),
        json={
            "person_id": "late",
            "expires_at": "2040-05-02T00:00:00+00:00",
        },
    ).status_code == 403


def test_duplicate_entry_and_question_length_are_safe_errors():
    app, _ = build_app()
    client = app.test_client()
    token = register_owner(client)
    payload = {"entry_id": "same", "kind": "diary", "content": "entry"}
    assert client.post("/entries", headers=auth(token), json=payload).status_code == 201
    duplicate = client.post("/entries", headers=auth(token), json=payload)
    assert duplicate.status_code == 409
    long_question = client.post(
        "/ask",
        headers=auth(token),
        json={"question": "x" * 2001},
    )
    assert long_question.status_code == 400


def test_security_headers_and_unknown_route():
    app, _ = build_app()
    response = app.test_client().get("/missing")

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Server" not in response.headers


def test_tiny_login_limit_can_be_reset():
    app, _ = build_app()
    app.extensions["limiter"].reset()
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    client = app.test_client()
    for _ in range(5):
        client.post(
            "/auth/login",
            json={"username": "lola", "password": "wrong-password-123"},
        )
    assert client.post(
        "/auth/login",
        json={"username": "lola", "password": "wrong-password-123"},
    ).status_code == 429
    app.extensions["limiter"].reset()
