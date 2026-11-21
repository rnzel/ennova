# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Offline tests for the local grounded-model adapter
from __future__ import annotations

import json
import logging
import os
import socket
import time
from pathlib import Path

import pytest

from app.ai.client import FakeModelClient, ModelPrompt, ModelResponse, PromptMessage
from app.ai.ollama import OllamaClient
from app.ai.prompts import SYSTEM_PROMPT, render_untrusted_block
from app.ai.provider import create_model_client
from app.errors import AIServiceUnavailable


class FakeSocket:
    def __init__(self) -> None:
        self.timeouts: list[float] = []

    def settimeout(self, timeout: float) -> None:
        self.timeouts.append(timeout)


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        read_error: Exception | None = None,
    ) -> None:
        self.body = body
        self.status = status
        self.read_error = read_error

    def read1(self, amount: int) -> bytes:
        if self.read_error is not None:
            raise self.read_error
        chunk, self.body = self.body[:amount], self.body[amount:]
        return chunk


class FakeConnection:
    def __init__(
        self,
        response: FakeResponse | None = None,
        *,
        connect_error: Exception | None = None,
        response_error: Exception | None = None,
    ) -> None:
        self.response = response
        self.connect_error = connect_error
        self.response_error = response_error
        self.sock = FakeSocket()
        self.request_args: tuple[object, ...] | None = None
        self.closed = False

    def connect(self) -> None:
        if self.connect_error is not None:
            raise self.connect_error

    def request(
        self,
        method: str,
        url: str,
        body: bytes,
        headers: dict[str, str],
    ) -> None:
        self.request_args = (method, url, body, headers)

    def getresponse(self) -> FakeResponse:
        if self.response_error is not None:
            raise self.response_error
        assert self.response is not None
        return self.response

    def close(self) -> None:
        self.closed = True


class FakeConnectionFactory:
    def __init__(self, *connections: FakeConnection) -> None:
        self.connections = list(connections)
        self.created: list[FakeConnection] = []
        self.calls: list[tuple[str, int | None, float]] = []

    def __call__(
        self, host: str, port: int | None, *, timeout: float
    ) -> FakeConnection:
        self.calls.append((host, port, timeout))
        connection = self.connections.pop(0)
        self.created.append(connection)
        return connection


def _client(
    response: FakeResponse | None = None,
    *,
    connection: FakeConnection | None = None,
    **kwargs: object,
) -> tuple[OllamaClient, FakeConnectionFactory]:
    selected = connection or FakeConnection(response)
    factory = FakeConnectionFactory(selected)
    kwargs.setdefault("host", "http://localhost:11434")
    client = OllamaClient(
        model="configured-test-model",
        connection_factory=factory,
        **kwargs,
    )
    return client, factory


def _prompt(
    *,
    content: str = '{"text":"A grounded answer.","citation_ids":["entry-1"]}',
    calls: list[object] | None = None,
    system: str = "Answer safely.",
    messages: tuple[PromptMessage, ...] | None = None,
    available_tools: tuple[str, ...] = ("search_entries",),
    deadline: float | None = None,
) -> tuple[ModelPrompt, bytes]:
    message: dict[str, object] = {
        "role": "assistant",
        "content": content,
    }
    if calls is not None:
        message["tool_calls"] = calls
    body = json.dumps({"message": message}, separators=(",", ":")).encode()
    return ModelPrompt(
        system,
        messages or (PromptMessage("user", "What did the permitted note say?"),),
        available_tools,
        deadline,
    ), body


def _tool_call(name: object, arguments: object) -> dict[str, object]:
    return {
        "function": {
            "name": name,
            "arguments": arguments,
        }
    }


def test_chat_request_uses_system_role_schema_tools_and_bounded_options():
    untrusted = render_untrusted_block(
        "untrusted_entry", "entry-1", "A permitted fictional detail."
    )
    prompt, body = _prompt(
        system="Keep the fixed safety rules.",
        messages=(
            PromptMessage("user", "What does the note say?"),
            PromptMessage("tool", untrusted),
        ),
        available_tools=("search_entries", "get_entry"),
    )
    client, factory = _client(FakeResponse(body))

    result = client.complete(prompt)

    request = factory.created[0].request_args
    assert result == ModelResponse("A grounded answer.", ("entry-1",))
    assert request is not None
    request_body = json.loads(request[2])
    assert [message["role"] for message in request_body["messages"]] == [
        "system",
        "user",
        "tool",
    ]
    assert request_body["messages"][0]["content"] == "Keep the fixed safety rules."
    assert "<untrusted_entry id=" in request_body["messages"][2]["content"]
    assert request_body["messages"][2]["content"].endswith(
        "</untrusted_entry>"
    )
    assert request_body["stream"] is False
    assert request_body["format"]["additionalProperties"] is False
    assert request_body["options"] == {
        "temperature": 0.1,
        "num_predict": 512,
        "num_ctx": 8192,
    }
    assert [tool["function"]["name"] for tool in request_body["tools"]] == [
        "search_entries",
        "get_entry",
    ]
    assert all("callable" not in repr(tool) for tool in request_body["tools"])


def test_tool_calls_are_returned_without_executing_them():
    prompt, body = _prompt(
        content="",
        calls=[_tool_call("search_entries", {"query": "garden"})],
    )
    client, factory = _client(FakeResponse(body))

    response = client.complete(prompt)

    assert response.tool_calls[0].name == "search_entries"
    assert response.tool_calls[0].arguments == {"query": "garden"}
    assert factory.created[0].request_args is not None


def test_unknown_tool_names_and_malformed_arguments_are_preserved_for_service_filtering():
    prompt, body = _prompt(
        content="",
        calls=[
            _tool_call("read_all_entries", {"asker": "nora"}),
            _tool_call("search_entries", "not-an-object"),
            {"not_function": True},
        ],
    )
    client, _ = _client(FakeResponse(body))

    response = client.complete(prompt)

    assert tuple(call.name for call in response.tool_calls) == (
        "read_all_entries",
        "search_entries",
        "",
    )
    assert response.tool_calls[1].arguments == "not-an-object"
    assert response.tool_calls[2].arguments is None


def test_small_model_response_schema_leak_is_normalized_for_search_entries():
    prompt, body = _prompt(
        content="",
        calls=[
            _tool_call(
                "search_entries",
                {"text": "search_entries", "citation_ids": []},
            )
        ],
        messages=(
            PromptMessage(
                "user",
                "What did he write about family?",
            ),
        ),
    )
    client, _ = _client(FakeResponse(body))

    response = client.complete(prompt)

    assert response.tool_calls[0].name == "search_entries"
    assert response.tool_calls[0].arguments == {
        "query": "What did he write about family?"
    }


@pytest.mark.parametrize(
    "content",
    (
        "not JSON",
        '{"text":"answer","citation_ids":[],"extra":"x"}',
        '{"text":"","citation_ids":[]}',
        '{"text":"answer","citation_ids":[1]}',
    ),
)
def test_malformed_final_json_fails_without_repair(content: str):
    prompt, body = _prompt(content=content)
    client, factory = _client(FakeResponse(body))

    with pytest.raises(AIServiceUnavailable) as error:
        client.complete(prompt)

    assert error.value.public_message == "The AI service is temporarily unavailable."
    assert len(factory.calls) == 1


def test_prompt_too_large_fails_before_network_and_never_drops_system_prompt():
    long_system = "safety instruction " * 400
    prompt, _ = _prompt(system=long_system)
    client, factory = _client(
        FakeResponse(b"{}"),
        num_ctx=1024,
        max_output_tokens=128,
    )

    with pytest.raises(AIServiceUnavailable):
        client.complete(prompt)

    assert factory.calls == []


def test_response_body_is_capped():
    prompt, body = _prompt()
    client, factory = _client(
        FakeResponse(body),
        num_ctx=1024,
        max_output_tokens=128,
        max_response_bytes=32,
    )

    with pytest.raises(AIServiceUnavailable):
        client.complete(prompt)

    assert factory.created[0].closed


def test_default_host_is_loopback_and_remote_requires_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "environment-test-model")
    monkeypatch.setenv("OLLAMA_ALLOW_REMOTE", "0")
    client = OllamaClient(connection_factory=FakeConnectionFactory())
    assert (client._hostname, client._port) == ("localhost", 11434)

    with pytest.raises(AIServiceUnavailable):
        OllamaClient(
            host="http://192.0.2.10:11434",
            model="configured-test-model",
            connection_factory=FakeConnectionFactory(),
        )

    monkeypatch.setenv("OLLAMA_ALLOW_REMOTE", "1")
    remote = OllamaClient(
        host="http://192.0.2.10:11434",
        model="configured-test-model",
        connection_factory=FakeConnectionFactory(),
    )
    assert (remote._hostname, remote._port) == ("192.0.2.10", 11434)


def test_redirect_is_not_followed():
    redirect_connection = FakeConnection(FakeResponse(b"", status=302))
    factory = FakeConnectionFactory(redirect_connection)
    prompt, _ = _prompt()
    client = OllamaClient(
        host="http://localhost:11434",
        model="configured-test-model",
        connect_timeout_seconds=15,
        connection_factory=factory,
    )

    with pytest.raises(AIServiceUnavailable):
        client.complete(prompt)

    assert factory.calls == [("localhost", 11434, 15.0)]
    assert redirect_connection.request_args[1] == "/api/chat"
    assert redirect_connection.closed


def test_system_proxy_settings_are_ignored(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy-canary.invalid:8888")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy-canary.invalid:8888")
    prompt, body = _prompt()
    connection = FakeConnection(FakeResponse(body))
    connections: list[tuple[str, int | None, float]] = []

    def connect_direct(
        host: str, port: int | None, *, timeout: float
    ) -> FakeConnection:
        connections.append((host, port, timeout))
        return connection

    monkeypatch.setattr(
        "app.ai.ollama.http.client.HTTPConnection", connect_direct
    )
    client = OllamaClient(
        host="http://localhost:11434",
        model="configured-test-model",
    )

    client.complete(prompt)

    assert connections[0][:2] == ("localhost", 11434)


def test_context_and_output_limits_come_from_backend_configuration(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("app.config.BaseConfig.OLLAMA_NUM_CTX", "4096")
    monkeypatch.setattr("app.config.BaseConfig.OLLAMA_MAX_OUTPUT_TOKENS", "256")
    prompt, body = _prompt()
    factory = FakeConnectionFactory(FakeConnection(FakeResponse(body)))
    client = OllamaClient(
        host="http://localhost:11434",
        model="configured-test-model",
        connection_factory=factory,
    )

    client.complete(prompt)

    request = factory.created[0].request_args
    assert request is not None
    options = json.loads(request[2])["options"]
    assert options["num_ctx"] == 4096
    assert options["num_predict"] == 256


def test_configured_timeouts_are_bounded_by_question_deadline():
    prompt, body = _prompt()
    connection = FakeConnection(FakeResponse(body))
    factory = FakeConnectionFactory(connection)
    client = OllamaClient(
        model="configured-test-model",
        connection_factory=factory,
        connect_timeout_seconds=12,
        read_timeout_seconds=25,
    )

    response = client.complete(prompt)

    assert response.text == "A grounded answer."
    assert factory.calls[0][2] == 12
    assert connection.sock.timeouts[0] == 25


def test_request_timeouts_are_clamped_to_remaining_question_deadline():
    prompt, body = _prompt(deadline=time.monotonic() + 5)
    connection = FakeConnection(FakeResponse(body))
    factory = FakeConnectionFactory(connection)
    client = OllamaClient(
        model="configured-test-model",
        connection_factory=factory,
        connect_timeout_seconds=12,
        read_timeout_seconds=25,
    )

    client.complete(prompt)

    assert 0 < factory.calls[0][2] <= 5
    assert 0 < connection.sock.timeouts[0] <= 5


@pytest.mark.parametrize(
    ("connection", "code"),
    (
        (
            FakeConnection(connect_error=ConnectionRefusedError("private down")),
            "connection_failed",
        ),
        (
            FakeConnection(response=FakeResponse(b"", status=404)),
            "http_404",
        ),
        (
            FakeConnection(
                response=FakeResponse(b"", read_error=socket.timeout("private timeout"))
            ),
            "request_timeout",
        ),
    ),
)
def test_server_down_model_not_pulled_and_timeout_return_unavailable(
    connection: FakeConnection,
    code: str,
):
    prompt, _ = _prompt()
    client, _ = _client(connection=connection)

    with pytest.raises(AIServiceUnavailable) as error:
        client.complete(prompt)

    assert error.value.public_message == "The AI service is temporarily unavailable."
    assert error.value.detail["code"] == code


def test_expired_total_deadline_prevents_connection():
    prompt, _ = _prompt(deadline=0.0)
    client, factory = _client(FakeResponse(b"{}"))

    with pytest.raises(AIServiceUnavailable) as error:
        client.complete(prompt)

    assert error.value.detail["code"] == "question_deadline"
    assert factory.calls == []


def test_failure_logging_and_exception_representations_exclude_canary(
    caplog: pytest.LogCaptureFixture,
):
    canaries = (
        "OLLAMA-KEY-CANARY",
        "OLLAMA-ERROR-CANARY",
        "OLLAMA-PROMPT-CANARY",
    )
    connection = FakeConnection(
        response_error=RuntimeError(
            f"server body {canaries[0]} {canaries[1]}"
        )
    )
    client, factory = _client(connection=connection)
    prompt, _ = _prompt(messages=(
        PromptMessage("user", f"Question includes {canaries[2]}"),
    ))
    caplog.set_level(logging.DEBUG)

    with pytest.raises(AIServiceUnavailable) as error:
        client.complete(prompt)

    assert str(error.value) == error.value.public_message
    assert type(error.value).__name__ in repr(error.value)
    assert error.value.code in repr(error.value)
    assert error.value.args == (
        error.value.public_message,
        error.value.code,
    )
    representations = (
        str(error.value),
        repr(error.value),
        repr(error.value.args),
        *(str(argument) for argument in error.value.args),
    )
    assert all(
        canary not in value
        for canary in canaries
        for value in representations
    )
    assert all(
        canary not in str(argument)
        for canary in canaries
        for argument in error.value.args
    )
    assert all(canary not in caplog.text for canary in canaries)
    assert f"server body {canaries[0]} {canaries[1]}" not in caplog.text
    assert len(factory.calls) == 1
    assert factory.created[0].request_args is not None
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == "ennova.ai.ollama"
    assert record.getMessage() == (
        "Ollama request failed: exception_class=RuntimeError code=request_failed"
    )
    assert record.exc_info is None


@pytest.mark.parametrize("provider", (None, "", "invalid"))
def test_missing_or_invalid_provider_fails_with_unavailable_reply(
    monkeypatch: pytest.MonkeyPatch,
    provider: str | None,
):
    if provider is None:
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.setattr("app.config.BaseConfig.LLM_PROVIDER", None)
    else:
        monkeypatch.setenv("LLM_PROVIDER", provider)

    with pytest.raises(AIServiceUnavailable) as error:
        create_model_client()

    assert error.value.public_message == "The AI service is temporarily unavailable."


def test_gemini_provider_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    with pytest.raises(AIServiceUnavailable) as error:
        create_model_client()

    assert error.value.public_message == "The AI service is temporarily unavailable."


def test_fake_provider_does_not_require_ollama_configuration(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setattr("app.config.BaseConfig.OLLAMA_MODEL", None)

    client = create_model_client()

    assert isinstance(client, FakeModelClient)
    with pytest.raises(AIServiceUnavailable):
        client.complete(_prompt()[0])


def test_ollama_model_is_required_and_has_no_code_default(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setattr("app.config.BaseConfig.OLLAMA_MODEL", None)
    factory = FakeConnectionFactory()

    with pytest.raises(AIServiceUnavailable) as error:
        OllamaClient(host="http://localhost:11434", connection_factory=factory)

    assert error.value.detail["code"] == "model_not_configured"
    assert factory.calls == []


def test_example_environment_exposes_provider_and_required_ollama_model():
    env_example = (
        Path(__file__).parents[1] / ".env.example"
    ).read_text(encoding="utf-8")

    assert "LLM_PROVIDER=" in env_example
    assert "OLLAMA_HOST=http://localhost:11434" in env_example
    assert "OLLAMA_MODEL=\n" in env_example


def test_provider_factory_selects_each_configured_client(
    monkeypatch: pytest.MonkeyPatch,
):
    sentinel = object()
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr("app.ai.ollama.OllamaClient", lambda: sentinel)
    assert create_model_client() is sentinel

    monkeypatch.setenv("LLM_PROVIDER", "fake")
    fake = FakeModelClient(())
    assert create_model_client(fake_client=fake) is fake


def test_config_and_example_environment_contain_no_gemini_settings():
    config = (Path(__file__).parents[1] / "app" / "config.py").read_text(
        encoding="utf-8"
    )
    env_example = (Path(__file__).parents[1] / ".env.example").read_text(
        encoding="utf-8"
    )

    assert "GEMINI" not in config
    assert "GEMINI" not in env_example


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_AI_TESTS") != "1",
    reason="set RUN_LIVE_AI_TESTS=1 to run live Ollama safety check",
)
def test_live_ollama_uses_only_fictional_permitted_material():
    client = OllamaClient()
    fictional_entry = render_untrusted_block(
        "untrusted_entry",
        "live-fictional-entry",
        "Lola planted three roses beside a garden path after the rain.",
    )
    response = client.complete(
        ModelPrompt(
            SYSTEM_PROMPT,
            (
                PromptMessage(
                    "user",
                    "What did Lola plant? Use only the permitted fictional note.",
                ),
                PromptMessage("tool", fictional_entry),
            ),
            (),
        )
    )

    assert response.text.strip()
    assert set(response.citation_ids) <= {"live-fictional-entry"}
    assert "I am the owner" not in response.text
