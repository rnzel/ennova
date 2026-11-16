# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Gemini model adapter for grounded scripting orchestration
from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Mapping

from google import genai
from google.genai import types

import app.config as app_config
from app.ai.client import ModelPrompt, ModelResponse, ToolCall
from app.errors import AIServiceUnavailable

_SDK_LOGGER = logging.getLogger("google.genai")
_SDK_LOGGER.setLevel(logging.ERROR)
_LOGGER = logging.getLogger("ennova.ai.gemini")
_LOGGER.setLevel(logging.WARNING)

_TOOL_SCHEMAS: dict[str, dict[str, object]] = {
    "search_entries": {
        "type": "function",
        "name": "search_entries",
        "description": "Search entries that have already passed access checks.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    "get_entry": {
        "type": "function",
        "name": "get_entry",
        "description": "Retrieve one entry already permitted for this question.",
        "parameters": {
            "type": "object",
            "properties": {"entry_id": {"type": "string"}},
            "required": ["entry_id"],
            "additionalProperties": False,
        },
    },
    "count_mentions": {
        "type": "function",
        "name": "count_mentions",
        "description": "Count permitted records mentioning a person.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    "get_letter": {
        "type": "function",
        "name": "get_letter",
        "description": "Retrieve a letter available to the fixed asker.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
            "additionalProperties": False,
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
_RETRYABLE_CODES = frozenset((429, *range(500, 600)))


class GeminiClient:
    """Implement ModelClient with stateless, schema-constrained Gemini calls."""

    question_timeout_seconds = 45.0

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        request_timeout_seconds: float = 10.0,
        question_timeout_seconds: float = 45.0,
        max_attempts: int = 3,
        sdk_client: object | None = None,
    ) -> None:
        """Create a configured client without exposing or logging credentials."""
        key = (
            api_key
            if api_key is not None
            else os.getenv("GEMINI_API_KEY")
            or app_config.BaseConfig.GEMINI_API_KEY
        )
        if not isinstance(key, str) or not key.strip():
            raise AIServiceUnavailable(
                detail="GEMINI_API_KEY must be configured in the backend environment"
            )
        if (
            request_timeout_seconds <= 0
            or question_timeout_seconds <= 0
            or max_attempts < 1
        ):
            raise ValueError("timeouts must be positive and attempts at least one.")
        configured_model = (
            model
            if model is not None
            else os.getenv("GEMINI_MODEL", app_config.BaseConfig.GEMINI_MODEL)
        )
        if not isinstance(configured_model, str) or not configured_model.strip():
            _log_failure_class("ConfigurationError", "model_not_configured")
            raise AIServiceUnavailable(
                detail={
                    "exception_class": "ConfigurationError",
                    "code": "model_not_configured",
                }
            )
        self._model = configured_model.strip()
        self._request_timeout_seconds = request_timeout_seconds
        self._max_attempts = max_attempts
        self.question_timeout_seconds = question_timeout_seconds
        if sdk_client is None:
            try:
                sdk_client = genai.Client(
                    api_key=key,
                    http_options=types.HttpOptions(
                        timeout=max(1, round(request_timeout_seconds * 1000)),
                        retry_options=types.HttpRetryOptions(
                            attempts=1,
                            http_status_codes=sorted(_RETRYABLE_CODES),
                        ),
                    ),
                )
            except Exception as error:
                _log_failure(error, _status_code(error))
                raise AIServiceUnavailable(
                    detail={"exception_class": type(error).__name__}
                ) from error
        self._client = sdk_client

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        """Call Gemini and strictly parse a JSON final response or tool calls."""
        if not isinstance(prompt, ModelPrompt):
            raise TypeError("prompt must be a ModelPrompt.")
        deadline = prompt.deadline_monotonic
        if deadline is None:
            deadline = time.monotonic() + self.question_timeout_seconds

        interaction = self._request(prompt, deadline)
        try:
            return _parse_interaction(interaction)
        except AIServiceUnavailable:
            _log_failure_class("MalformedResponse", "invalid_response")
            raise
        except Exception as error:
            _log_failure(error, _status_code(error))
            raise AIServiceUnavailable(
                detail={"exception_class": type(error).__name__}
            ) from error

    def _request(self, prompt: ModelPrompt, deadline: float) -> object:
        tools = [
            _TOOL_SCHEMAS[name]
            for name in prompt.available_tools
            if name in _TOOL_SCHEMAS
        ]
        for attempt in range(self._max_attempts):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AIServiceUnavailable(detail="question deadline exceeded")
            timeout = min(self._request_timeout_seconds, remaining)
            try:
                return self._client.interactions.create(
                    model=self._model,
                    input=_serialize_messages(prompt),
                    system_instruction=prompt.system_prompt,
                    tools=tools,
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": _RESPONSE_SCHEMA,
                    },
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 512,
                    },
                    store=False,
                    automatic_continuation=False,
                    timeout=timeout,
                )
            except Exception as error:
                status_code = _status_code(error)
                _log_failure(error, status_code)
                if (
                    not _is_retryable(status_code)
                    or attempt + 1 >= self._max_attempts
                ):
                    raise AIServiceUnavailable(
                        detail={
                            "exception_class": type(error).__name__,
                            "code": status_code,
                        }
                    ) from error
                delay = min(0.25 * (2**attempt), 1.0)
                remaining = deadline - time.monotonic()
                if remaining <= delay:
                    raise AIServiceUnavailable(
                        detail="question deadline exceeded during retry"
                    ) from error
                time.sleep(delay)
        raise AIServiceUnavailable(detail="Gemini retry limit reached")


def _serialize_messages(prompt: ModelPrompt) -> str:
    messages = [
        {"role": message.role, "content": message.content}
        for message in prompt.messages
    ]
    return json.dumps(messages, ensure_ascii=False, separators=(",", ":"))


def _parse_interaction(interaction: object) -> ModelResponse:
    status = getattr(interaction, "status", None)
    if status not in (None, "completed", "requires_action"):
        raise AIServiceUnavailable(detail="Gemini interaction was not completed")
    steps = getattr(interaction, "steps", None)
    calls: list[ToolCall] = []
    for step in steps or ():
        if getattr(step, "type", None) == "function_call":
            name = getattr(step, "name", "")
            arguments = getattr(step, "arguments", None)
            calls.append(
                ToolCall(name if isinstance(name, str) else "", arguments)
            )
        if getattr(step, "error", None) is not None:
            raise AIServiceUnavailable(detail="Gemini returned a blocked response")
    if calls:
        return ModelResponse("", tool_calls=tuple(calls))

    output = getattr(interaction, "output_text", None)
    if not isinstance(output, str) or not output.strip():
        raise AIServiceUnavailable(detail="Gemini returned an empty response")
    decoded = json.loads(output)
    if (
        not isinstance(decoded, Mapping)
        or set(decoded) != {"text", "citation_ids"}
        or not isinstance(decoded["text"], str)
        or not isinstance(decoded["citation_ids"], list)
        or any(not isinstance(item, str) for item in decoded["citation_ids"])
        or not decoded["text"].strip()
    ):
        raise AIServiceUnavailable(detail="Gemini response did not match its schema")
    return ModelResponse(
        decoded["text"],
        tuple(decoded["citation_ids"]),
    )


def _status_code(error: Exception) -> int | None:
    for attribute in ("status_code", "code", "status"):
        value = getattr(error, attribute, None)
        if isinstance(value, int) and 100 <= value <= 599:
            return value
    return None


def _is_retryable(status_code: int | None) -> bool:
    return status_code == 429 or (
        status_code is not None and 500 <= status_code <= 599
    )


def _log_failure(error: Exception, code: int | None) -> None:
    _log_failure_class(type(error).__name__, code)


def _log_failure_class(exception_class: str, code: int | str | None) -> None:
    _LOGGER.warning(
        "Gemini request failed: exception_class=%s code=%s",
        exception_class,
        code if code is not None else "unknown",
    )


__all__ = ["GeminiClient"]
