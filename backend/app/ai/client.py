# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Model interface and deterministic test double
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from app.errors import AIServiceUnavailable


@dataclass(frozen=True, slots=True)
class PromptMessage:
    """One user or tool message in a model interaction."""

    role: Literal["user", "tool"]
    content: str


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A model-proposed tool name and untrusted argument object."""

    name: str
    arguments: object


@dataclass(frozen=True, slots=True)
class ModelPrompt:
    """The full system prompt, conversation, and available tool names."""

    system_prompt: str
    messages: tuple[PromptMessage, ...]
    available_tools: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Model text, citation IDs, and optional tool calls."""

    text: str
    citation_ids: tuple[str, ...] = ()
    tool_calls: tuple[ToolCall, ...] = ()


class ModelClient(Protocol):
    """Interface for a model that only receives prepared, permitted prompts."""

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        """Return a structured response for one prompt."""


class FakeModelClient:
    """Scripted model test double that records every prompt it receives."""

    def __init__(self, responses: tuple[ModelResponse, ...]) -> None:
        """Create a deterministic response sequence."""
        if not isinstance(responses, tuple) or any(
            not isinstance(response, ModelResponse) for response in responses
        ):
            raise TypeError("responses must be a tuple of ModelResponse values.")
        self._responses = responses
        self.prompts: list[ModelPrompt] = []
        self._next_response = 0

    def complete(self, prompt: ModelPrompt) -> ModelResponse:
        """Record a prompt and return the next scripted response."""
        if not isinstance(prompt, ModelPrompt):
            raise TypeError("prompt must be a ModelPrompt.")
        self.prompts.append(prompt)
        if self._next_response >= len(self._responses):
            raise AIServiceUnavailable(detail="fake response sequence exhausted")
        response = self._responses[self._next_response]
        self._next_response += 1
        return response
