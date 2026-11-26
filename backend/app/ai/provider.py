# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Fail-closed model provider selection
from __future__ import annotations

import os

import app.config as app_config
from app.ai.client import FakeModelClient, ModelClient
from app.errors import AIServiceUnavailable


def create_model_client(
    *, fake_client: ModelClient | None = None
) -> ModelClient:
    """Select a configured provider; never silently fall back to another one."""
    provider = os.getenv("LLM_PROVIDER", app_config.BaseConfig.LLM_PROVIDER)
    if not isinstance(provider, str):
        raise AIServiceUnavailable(detail="LLM_PROVIDER is not configured")
    selected = provider.strip().casefold()
    if selected == "fake":
        if fake_client is not None:
            return fake_client
        return FakeModelClient(())
    if selected == "ollama":
        from app.ai.ollama import OllamaClient

        return OllamaClient()
    if selected == "groq":
        from app.ai.groq import GroqClient

        return GroqClient()
    raise AIServiceUnavailable(detail="LLM_PROVIDER is not configured")


__all__ = ["create_model_client"]
