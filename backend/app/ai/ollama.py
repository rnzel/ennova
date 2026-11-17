# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Local model adapter for grounded scripting orchestration
from __future__ import annotations

import http.client
import ipaddress
import json
import logging
import math
import os
import socket
import time
from collections.abc import Callable, Mapping
from typing import Protocol
from urllib.parse import SplitResult, urlsplit

import app.config as app_config
from app.ai.client import ModelPrompt, ModelResponse, ToolCall
from app.errors import AIServiceUnavailable

_LOGGER = logging.getLogger("ennova.ai.ollama")
_LOGGER.setLevel(logging.WARNING)

_TOOL_SCHEMAS: dict[str, dict[str, object]] = {
    "search_entries": {
        "type": "function",
        "function": {
            "name": "search_entries",
            "description": "Search entries that have already passed access checks.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    "get_entry": {
        "type": "function",
        "function": {
            "name": "get_entry",
            "description": "Retrieve one entry already permitted for this question.",
            "parameters": {
                "type": "object",
                "properties": {"entry_id": {"type": "string"}},
                "required": ["entry_id"],
                "additionalProperties": False,
            },
        },
    },
    "count_mentions": {
        "type": "function",
        "function": {
            "name": "count_mentions",
            "description": "Count permitted records mentioning a person.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    "get_letter": {
        "type": "function",
        "function": {
            "name": "get_letter",
            "description": "Retrieve a letter available to the fixed asker.",
            "parameters": {
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
                "additionalProperties": False,
            },
        },
    },
}
_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "citation_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["text", "citation_ids"],
    "additionalProperties": False,
}
_MAX_READ_CHUNK = 16_384
_CONTEXT_SAFETY_TOKENS = 128
_MAX_REQUEST_TIMEOUT_SECONDS = 120.0
_MAX_QUESTION_TIMEOUT_SECONDS = 300.0


class _Response(Protocol):
    status: int

    def read1(self, amount: int) -> bytes:
        """Read one bounded response chunk."""


class _Connection(Protocol):
    sock: socket.socket | None

    def connect(self) -> None:
        """Connect to the configured endpoint."""

    def request(
        self, method: str, url: str, body: bytes, headers: dict[str, str]
    ) -> None:
        """Send one HTTP request."""

    def getresponse(self) -> _Response:
        """Return the response headers and bounded body reader."""

    def close(self) -> None:
        """Close the connection."""


class _ProviderFailure(Exception):
    def __init__(self, exception_class: str, code: str) -> None:
        self.exception_class = exception_class
        self.code = code


class OllamaClient:
    """Implement ModelClient with Ollama's local chat and JSON-schema APIs."""

    question_timeout_seconds = 45.0

    def __init__(
        self,
        *,
        host: str | None = None,
        model: str | None = None,
        allow_remote: bool | None = None,
        num_ctx: int | str | None = None,
        max_output_tokens: int | str | None = None,
        request_timeout_seconds: float | str | None = None,
        connect_timeout_seconds: float | str | None = None,
        read_timeout_seconds: float | str | None = None,
        max_response_bytes: int | str | None = None,
        question_timeout_seconds: float | str | None = None,
        connection_factory: Callable[..., _Connection] | None = None,
    ) -> None:
        """Create a client from backend configuration without logging its data."""
        configured_host = (
            os.getenv("OLLAMA_HOST", app_config.BaseConfig.OLLAMA_HOST)
            if host is None
            else host
        )
        configured_model = (
            os.getenv("OLLAMA_MODEL", app_config.BaseConfig.OLLAMA_MODEL)
            if model is None
            else model
        )
        remote_enabled = (
            (
                os.getenv("OLLAMA_ALLOW_REMOTE") == "1"
                if "OLLAMA_ALLOW_REMOTE" in os.environ
                else app_config.BaseConfig.OLLAMA_ALLOW_REMOTE
            )
            if allow_remote is None
            else allow_remote
        )
        try:
            if not isinstance(configured_host, str):
                raise _ProviderFailure("ConfigurationError", "invalid_host")
            endpoint = _parse_endpoint(configured_host, remote_enabled)
            if (
                not isinstance(configured_model, str)
                or not configured_model.strip()
            ):
                raise _ProviderFailure("ConfigurationError", "model_not_configured")
            parsed_num_ctx = _positive_int(
                app_config.BaseConfig.OLLAMA_NUM_CTX
                if num_ctx is None
                else num_ctx,
                "invalid_context_size",
            )
            parsed_output_cap = _positive_int(
                app_config.BaseConfig.OLLAMA_MAX_OUTPUT_TOKENS
                if max_output_tokens is None
                else max_output_tokens,
                "invalid_output_limit",
            )
            parsed_response_cap = _positive_int(
                app_config.BaseConfig.OLLAMA_MAX_RESPONSE_BYTES
                if max_response_bytes is None
                else max_response_bytes,
                "invalid_response_limit",
            )
            request_timeout = _bounded_positive_float(
                app_config.BaseConfig.OLLAMA_REQUEST_TIMEOUT_SECONDS
                if request_timeout_seconds is None
                else request_timeout_seconds,
                "invalid_request_timeout",
                _MAX_REQUEST_TIMEOUT_SECONDS,
            )
            connect_timeout = _positive_float(
                app_config.BaseConfig.OLLAMA_CONNECT_TIMEOUT_SECONDS
                if connect_timeout_seconds is None
                else connect_timeout_seconds,
                "invalid_connect_timeout",
            )
            read_timeout = _positive_float(
                request_timeout
                if read_timeout_seconds is None
                else read_timeout_seconds,
                "invalid_read_timeout",
            )
            if read_timeout > _MAX_REQUEST_TIMEOUT_SECONDS:
                raise _ProviderFailure(
                    "ConfigurationError", "invalid_read_timeout"
                )
            question_timeout = _bounded_positive_float(
                app_config.BaseConfig.OLLAMA_QUESTION_TIMEOUT_SECONDS
                if question_timeout_seconds is None
                else question_timeout_seconds,
                "invalid_question_timeout",
                _MAX_QUESTION_TIMEOUT_SECONDS,
            )
            if parsed_output_cap + _CONTEXT_SAFETY_TOKENS >= parsed_num_ctx:
                raise _ProviderFailure(
                    "ConfigurationError", "invalid_context_budget"
                )
        except _ProviderFailure as failure:
            _raise_unavailable(failure)

        self._scheme, self._hostname, self._port = endpoint
        self._model = configured_model.strip()
        self._num_ctx = parsed_num_ctx
        self._max_output_tokens = parsed_output_cap
        self._connect_timeout_seconds = connect_timeout
        self._read_timeout_seconds = read_timeout
        self._max_response_bytes = parsed_response_cap
        self.question_timeout_seconds = question_timeout
        self._connection_factory = connection_factory or (
            http.client.HTTPSConnection
            if self._scheme == "https"
            else http.client.HTTPConnection
        )

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        """Request one strict JSON answer or return tool calls for manual execution."""
        if not isinstance(prompt, ModelPrompt):
            raise TypeError("prompt must be a ModelPrompt.")
        try:
            deadline = prompt.deadline_monotonic
            if deadline is None:
                deadline = time.monotonic() + self.question_timeout_seconds
            if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
                raise _ProviderFailure("InvalidPrompt", "invalid_deadline")
            if deadline <= time.monotonic():
                raise _ProviderFailure("TimeoutError", "question_deadline")

            body = _serialize_request(
                prompt,
                self._model,
                self._num_ctx,
                self._max_output_tokens,
            )
            if _estimate_prompt_tokens(body) + self._max_output_tokens + (
                _CONTEXT_SAFETY_TOKENS
            ) > self._num_ctx:
                raise _ProviderFailure("PromptTooLarge", "context_limit")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _ProviderFailure("TimeoutError", "question_deadline")
            connection = self._connection_factory(
                self._hostname,
                self._port,
                timeout=min(self._connect_timeout_seconds, remaining),
            )
            try:
                connection.connect()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _ProviderFailure("TimeoutError", "question_deadline")
                if connection.sock is None:
                    raise _ProviderFailure("ConnectionError", "connection_failed")
                connection.sock.settimeout(
                    min(self._read_timeout_seconds, remaining)
                )
                connection.request(
                    "POST",
                    "/api/chat",
                    body,
                    {
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
                response = connection.getresponse()
                if response.status != 200:
                    raise _ProviderFailure(
                        "HTTPError", f"http_{response.status}"
                    )
                response_body = _read_bounded_response(
                    response,
                    connection,
                    deadline,
                    self._read_timeout_seconds,
                    self._max_response_bytes,
                )
            finally:
                connection.close()

            return _parse_response(response_body)
        except _ProviderFailure as failure:
            _raise_unavailable(failure)
        except Exception as error:
            _raise_unavailable(
                _ProviderFailure(type(error).__name__, _exception_code(error))
            )


def _serialize_request(
    prompt: ModelPrompt,
    model: str,
    num_ctx: int,
    max_output_tokens: int,
) -> bytes:
    messages = [{"role": "system", "content": prompt.system_prompt}]
    messages.extend(
        {"role": message.role, "content": message.content}
        for message in prompt.messages
    )
    tools = [
        _TOOL_SCHEMAS[name]
        for name in prompt.available_tools
        if name in _TOOL_SCHEMAS
    ]
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "format": _RESPONSE_SCHEMA,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": max_output_tokens,
            "num_ctx": num_ctx,
        },
    }
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _estimate_prompt_tokens(body: bytes) -> int:
    """Conservatively estimate input tokens from the complete serialized request."""
    return len(body)


def _read_bounded_response(
    response: _Response,
    connection: _Connection,
    deadline: float,
    read_timeout_seconds: float,
    max_response_bytes: int,
) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _ProviderFailure("TimeoutError", "question_deadline")
        if connection.sock is None:
            raise _ProviderFailure("ConnectionError", "connection_failed")
        connection.sock.settimeout(min(read_timeout_seconds, remaining))
        chunk = response.read1(min(_MAX_READ_CHUNK, max_response_bytes + 1 - total))
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        total += len(chunk)
        if total > max_response_bytes:
            raise _ProviderFailure("ResponseTooLarge", "response_size_limit")


def _parse_response(response_body: bytes) -> ModelResponse:
    try:
        decoded = json.loads(response_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _ProviderFailure("MalformedResponse", "malformed_response") from None
    if not isinstance(decoded, Mapping) or "error" in decoded:
        raise _ProviderFailure("MalformedResponse", "provider_error")
    message = decoded.get("message")
    if not isinstance(message, Mapping):
        raise _ProviderFailure("MalformedResponse", "malformed_response")

    raw_calls = message.get("tool_calls", [])
    if not isinstance(raw_calls, list):
        raise _ProviderFailure("MalformedResponse", "malformed_tool_calls")
    if raw_calls:
        calls: list[ToolCall] = []
        for raw_call in raw_calls:
            function = raw_call.get("function") if isinstance(raw_call, Mapping) else None
            if not isinstance(function, Mapping):
                calls.append(ToolCall("", None))
                continue
            name = function.get("name")
            calls.append(
                ToolCall(
                    name if isinstance(name, str) else "",
                    function.get("arguments"),
                )
            )
        return ModelResponse("", tool_calls=tuple(calls))

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise _ProviderFailure("MalformedResponse", "empty_response")
    try:
        answer = json.loads(content)
    except json.JSONDecodeError:
        raise _ProviderFailure("MalformedResponse", "malformed_response") from None
    if (
        not isinstance(answer, Mapping)
        or set(answer) != {"text", "citation_ids"}
        or not isinstance(answer["text"], str)
        or not answer["text"].strip()
        or not isinstance(answer["citation_ids"], list)
        or any(not isinstance(item, str) for item in answer["citation_ids"])
    ):
        raise _ProviderFailure("MalformedResponse", "schema_mismatch")
    return ModelResponse(answer["text"], tuple(answer["citation_ids"]))


def _parse_endpoint(host: str, allow_remote: bool) -> tuple[str, str, int | None]:
    try:
        parsed: SplitResult = urlsplit(host)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise _ProviderFailure("ConfigurationError", "invalid_host") from None
    if (
        parsed.scheme not in ("http", "https")
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise _ProviderFailure("ConfigurationError", "invalid_host")
    if not _is_loopback(hostname) and allow_remote is not True:
        raise _ProviderFailure("ConfigurationError", "remote_host_not_allowed")
    return parsed.scheme, hostname, port


def _is_loopback(hostname: str) -> bool:
    if hostname.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _positive_int(value: object, failure_code: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise _ProviderFailure("ConfigurationError", failure_code) from None
    if parsed <= 0:
        raise _ProviderFailure("ConfigurationError", failure_code)
    return parsed


def _positive_float(value: object, failure_code: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise _ProviderFailure("ConfigurationError", failure_code) from None
    if not math.isfinite(parsed) or parsed <= 0:
        raise _ProviderFailure("ConfigurationError", failure_code)
    return parsed


def _bounded_positive_float(
    value: object, failure_code: str, maximum: float
) -> float:
    parsed = _positive_float(value, failure_code)
    if parsed > maximum:
        raise _ProviderFailure("ConfigurationError", failure_code)
    return parsed


def _exception_code(error: Exception) -> str:
    if isinstance(error, (socket.timeout, TimeoutError)):
        return "request_timeout"
    if isinstance(error, OSError):
        return "connection_failed"
    if isinstance(error, http.client.HTTPException):
        return "http_protocol_error"
    return "request_failed"


def _raise_unavailable(failure: _ProviderFailure) -> None:
    _LOGGER.warning(
        "Ollama request failed: exception_class=%s code=%s",
        failure.exception_class,
        failure.code,
    )
    raise AIServiceUnavailable(
        detail={
            "exception_class": failure.exception_class,
            "code": failure.code,
        }
    ) from None


__all__ = ["OllamaClient"]
