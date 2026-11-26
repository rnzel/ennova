"""Groq SDK adapter for ENNOVA's provider-neutral grounded model interface."""
from __future__ import annotations

import json
import os
import time
from typing import Any

import app.config as app_config
from app.ai.client import ModelPrompt, ModelResponse, ToolCall
from app.ai.schemas import _RESPONSE_SCHEMA, _TOOL_SCHEMAS
from app.errors import AIServiceUnavailable

_DEFAULT_MODEL = "openai/gpt-oss-120b"
_MAX_TIMEOUT_SECONDS = 300.0


class GroqClient:
    """Call the official Groq SDK without exposing credentials or raw errors."""

    question_timeout_seconds = 45.0

    def __init__(self, *, api_key=None, model=None, timeout_seconds=None, client=None):
        key = os.getenv("GROQ_API_KEY", app_config.BaseConfig.GROQ_API_KEY) if api_key is None else api_key
        selected_model = os.getenv("GROQ_MODEL", app_config.BaseConfig.GROQ_MODEL) if model is None else model
        configured_timeout = (os.getenv("GROQ_QUESTION_TIMEOUT_SECONDS", app_config.BaseConfig.GROQ_QUESTION_TIMEOUT_SECONDS)
                              if timeout_seconds is None else timeout_seconds)
        if not isinstance(key, str) or not key.strip():
            raise AIServiceUnavailable(detail="Groq API key is not configured")
        if not isinstance(selected_model, str) or not selected_model.strip():
            raise AIServiceUnavailable(detail="Groq model is not configured")
        try:
            timeout = float(configured_timeout)
            if not 0 < timeout <= _MAX_TIMEOUT_SECONDS:
                raise ValueError
        except (TypeError, ValueError):
            raise AIServiceUnavailable(detail="invalid Groq timeout configuration") from None
        if client is None:
            try:
                from groq import Groq
            except ImportError:
                raise AIServiceUnavailable(detail="Groq SDK is unavailable") from None
            try:
                client = Groq(api_key=key.strip(), timeout=timeout, max_retries=0)
            except Exception as error:
                raise AIServiceUnavailable(detail=type(error).__name__) from None
        self._client = client
        self._model = selected_model.strip()
        self.question_timeout_seconds = timeout

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        if not isinstance(prompt, ModelPrompt):
            raise TypeError("prompt must be a ModelPrompt.")
        deadline = prompt.deadline_monotonic
        if deadline is None:
            deadline = time.monotonic() + self.question_timeout_seconds
        if not isinstance(deadline, (int, float)) or deadline <= time.monotonic():
            raise AIServiceUnavailable(detail="model question deadline exceeded")
        messages = [{"role": "system", "content": _response_instruction(prompt.system_prompt)}]
        for message in prompt.messages:
            # Our orchestration stores app-produced tool results without SDK call IDs.
            # Reframe them as application evidence in a user message, never as a raw
            # provider tool message that could be detached from the executed tool.
            content = message.content
            role = message.role
            if role == "tool":
                role = "user"
                content = "Application-retrieved tool results (untrusted data):\n" + content
            messages.append({"role": role, "content": content})

        tool_names = tuple(name for name in prompt.available_tools if name in _TOOL_SCHEMAS)
        request: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.1,
            "max_completion_tokens": 512,
            "timeout": max(0.001, deadline - time.monotonic()),
        }
        if tool_names:
            request["tools"] = [_TOOL_SCHEMAS[name] for name in tool_names]
            request["tool_choice"] = "auto"
        else:
            # Groq does not support tool use and structured outputs in one request.
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "ennova_answer", "strict": True, "schema": _RESPONSE_SCHEMA},
            }
        try:
            result = self._client.chat.completions.create(**request)
        except Exception as error:
            # SDK exceptions can include request details; expose only their class.
            raise AIServiceUnavailable(detail=type(error).__name__) from None
        if time.monotonic() >= deadline:
            raise AIServiceUnavailable(detail="model question deadline exceeded")
        return _parse_completion(result)


def _response_instruction(system_prompt: str) -> str:
    return system_prompt + (
        " Return the final answer only as a JSON object with exactly two fields: "
        '"text" (string) and "citation_ids" (array of entry ID strings). '
        "When requesting a tool, use the provided function tool call instead."
    )


def _parse_completion(result: object) -> ModelResponse:
    try:
        choices = result.choices
        if not isinstance(choices, (tuple, list)) or len(choices) != 1:
            raise ValueError
        choice = choices[0]
        message = choice.message
        raw_calls = getattr(message, "tool_calls", None) or ()
        calls: list[ToolCall] = []
        for raw in raw_calls:
            function = raw.function
            arguments = function.arguments
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            calls.append(ToolCall(function.name, arguments))
        if calls:
            return ModelResponse("", tool_calls=tuple(calls))
        content = message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError
        decoded = json.loads(content)
        if (not isinstance(decoded, dict) or set(decoded) != {"text", "citation_ids"}
                or not isinstance(decoded["text"], str) or not decoded["text"].strip()
                or not isinstance(decoded["citation_ids"], list)
                or any(not isinstance(item, str) for item in decoded["citation_ids"])):
            raise ValueError
        return ModelResponse(decoded["text"], tuple(decoded["citation_ids"]))
    except Exception:
        raise AIServiceUnavailable(detail="malformed Groq response") from None


__all__ = ["GroqClient"]
