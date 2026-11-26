import time
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app import create_app
from app.ai.client import ModelPrompt, PromptMessage
from app.ai.groq import GroqClient
from app.ai.provider import create_model_client
from app.ai.summaries import FakeSummarizer, InMemorySummaryStore
from app.domain.diary import InMemoryEntryRepository
from app.errors import AIServiceUnavailable
from app.policy import AccessBatchResult, AppFacts, parse
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService
from app.services.owner_grounded_qa import OwnerGroundedQAService


def completion(content=None, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")])


class MockCompletions:
    def __init__(self, *results):
        self.results = list(results)
        self.requests = []

    def create(self, **request):
        self.requests.append(request)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def sdk_client(completions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_groq_provider_selection_and_missing_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr("app.config.BaseConfig.GROQ_API_KEY", None)
    with pytest.raises(AIServiceUnavailable):
        GroqClient()
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    sentinel = object()
    monkeypatch.setattr("app.ai.groq.GroqClient", lambda: sentinel)
    assert create_model_client() is sentinel


def test_groq_owner_style_json_response_and_model_configuration():
    api = MockCompletions(completion('{"text":"A grounded answer.","citation_ids":["entry-1"]}'))
    client = GroqClient(api_key="test-key", model="openai/gpt-oss-120b", client=sdk_client(api))
    prompt = ModelPrompt("Owner instructions", (PromptMessage("user", "question and retrieved evidence"),), ())
    result = client.complete(prompt)
    assert (result.text, result.citation_ids) == ("A grounded answer.", ("entry-1",))
    request = api.requests[0]
    assert request["model"] == "openai/gpt-oss-120b"
    assert request["response_format"]["type"] == "json_schema"
    assert request["messages"][0]["role"] == "system"


def test_groq_beneficiary_tool_call_and_safe_tool_result_mapping():
    first = SimpleNamespace(id="call-1", function=SimpleNamespace(
        name="search_entries", arguments='{"query":"family"}'))
    api = MockCompletions(
        completion(None, [first]),
        completion('{"text":"Permitted result.","citation_ids":["entry-1"]}'),
    )
    client = GroqClient(api_key="test-key", client=sdk_client(api))
    prompt = ModelPrompt("Policy-filtered instructions", (
        PromptMessage("user", "question"),
        PromptMessage("tool", "<untrusted_entry id=\"entry-1\">allowed evidence</untrusted_entry>"),
    ), ("search_entries",))
    result = client.complete(prompt)
    assert result.tool_calls[0].name == "search_entries"
    request = api.requests[0]
    assert request["tools"][0]["function"]["name"] == "search_entries"
    assert "response_format" not in request  # Groq disallows tools + structured output.
    final = client.complete(ModelPrompt("Policy-filtered instructions", (
        PromptMessage("user", "question"),
        PromptMessage("tool", "permitted evidence"),
    ), ("search_entries",)))
    assert final.text == "Permitted result."
    # App-generated tool output is untrusted application evidence, not an SDK tool
    # message detached from a Groq tool_call_id.
    second_request = api.requests[1]
    assert second_request["messages"][2]["role"] == "user"
    assert "untrusted data" in second_request["messages"][2]["content"]


class RateLimitError(Exception):
    pass


@pytest.mark.parametrize("error", [TimeoutError("deadline"), RateLimitError("rate limited")])
def test_groq_api_errors_fail_closed_without_raw_error(error):
    client = GroqClient(api_key="test-key", client=sdk_client(MockCompletions(error)))
    with pytest.raises(AIServiceUnavailable):
        client.complete(ModelPrompt("instructions", (PromptMessage("user", "question"),), ()))


@pytest.mark.parametrize("payload", ["not json", '{"text":"ok","citation_ids":[4]}', "{}"])
def test_groq_malformed_responses_are_rejected(payload):
    client = GroqClient(api_key="test-key", client=sdk_client(MockCompletions(completion(payload))))
    with pytest.raises(AIServiceUnavailable):
        client.complete(ModelPrompt("instructions", (PromptMessage("user", "question"),), ()))


def test_groq_prompt_deadline_is_enforced_before_request():
    api = MockCompletions()
    client = GroqClient(api_key="test-key", client=sdk_client(api))
    with pytest.raises(AIServiceUnavailable):
        client.complete(ModelPrompt("instructions", (PromptMessage("user", "q"),), (), time.monotonic() - 1))
    assert not api.requests


def test_owner_chatbot_uses_groq_adapter_and_validates_citations():
    api = MockCompletions(completion(
        '{"text":"You recorded a memorable university day.","citation_ids":["uni-day","other-owner-entry"]}'
    ))
    model = GroqClient(api_key="test-key", client=sdk_client(api))
    app = create_app(model_client=model, summarizer=FakeSummarizer(), config_overrides={
        "TESTING": True, "JWT_SECRET_KEY": "t" * 32, "APP_TIMEZONE": "UTC"
    })
    client = app.test_client()
    registration = client.post("/auth/register-owner", json={
        "username": "groq_owner", "email": "groq-owner@example.test",
        "password": "fictional-password-123",
    })
    assert registration.status_code == 201
    token = client.post("/auth/login", json={
        "username": "groq_owner", "password": "fictional-password-123",
    }).get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/entries", headers=headers, json={
        "entry_id": "uni-day", "kind": "diary", "content": "My university visit was memorable. #university"
    }).status_code == 201
    response = client.post("/owner/ask", headers=headers, json={"question": "What happened at university?"})
    assert api.requests, response.get_json()
    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert len(payload["citations"]) == 1
    assert payload["citations"][0]["entry_id"] == "uni-day"
    date.fromisoformat(payload["citations"][0]["date"])
    assert "other-owner-entry" not in str(payload["citations"])


def test_beneficiary_chatbot_uses_local_tool_execution_after_access_check():
    tool_call = SimpleNamespace(id="call-1", function=SimpleNamespace(
        name="search_entries", arguments='{"query":"family"}'))
    api = MockCompletions(
        completion(None, [tool_call]),
        completion('{"text":"A permitted family record.","citation_ids":["family-note"]}'),
    )
    model = GroqClient(api_key="test-key", client=sdk_client(api))
    diary = DiaryService(InMemoryEntryRepository())
    diary.add_diary_entry("owner-id", "family-note", "A family memory. #family",
                          datetime(2040, 1, 2, tzinfo=timezone.utc))

    class AllowingBridge:
        def evaluate_many(self, policy, facts, *, access_requests, letter_status_requests):
            return AccessBatchResult(("deny", "deny", "allow"), ())

    service = GroundedQAService(diary, AllowingBridge(), model, InMemorySummaryStore())
    answer = service.answer("What about family?", owner_id="owner-id", asker="maria",
        policy_source="protocol maria:\n", app_facts=AppFacts(), today=date(2040, 1, 2))
    assert answer.text == "A permitted family record."
    assert tuple(c.entry_id for c in answer.citations) == ("family-note",)
    assert api.requests[0]["tools"][0]["function"]["name"] == "search_entries"


def test_groq_owner_no_record_path_does_not_call_provider():
    api = MockCompletions()
    model = GroqClient(api_key="test-key", client=sdk_client(api))
    service = OwnerGroundedQAService(DiaryService(InMemoryEntryRepository()), model)
    result = service.answer("Did I mention a fictional event?", owner_id="owner-a", today=date(2040, 1, 2))
    assert result.no_record is True
    assert not api.requests
