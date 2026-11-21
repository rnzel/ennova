# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Infrastructure / configuration
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend-local development configuration without overriding deployment env.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "UTC")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AIVEN_CA_PATH = os.getenv("AIVEN_CA_PATH", "")
    SWIPL_EXECUTABLE = os.getenv("SWIPL_EXECUTABLE", "swipl")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
    OLLAMA_ALLOW_REMOTE = os.getenv("OLLAMA_ALLOW_REMOTE") == "1"
    OLLAMA_NUM_CTX = os.getenv("OLLAMA_NUM_CTX", "8192")
    OLLAMA_MAX_OUTPUT_TOKENS = os.getenv("OLLAMA_MAX_OUTPUT_TOKENS", "512")
    OLLAMA_REQUEST_TIMEOUT_SECONDS = os.getenv(
        "OLLAMA_REQUEST_TIMEOUT_SECONDS", "30"
    )
    OLLAMA_QUESTION_TIMEOUT_SECONDS = os.getenv(
        "OLLAMA_QUESTION_TIMEOUT_SECONDS", "45"
    )
    OLLAMA_CONNECT_TIMEOUT_SECONDS = os.getenv(
        "OLLAMA_CONNECT_TIMEOUT_SECONDS", "15"
    )
    OLLAMA_READ_TIMEOUT_SECONDS = os.getenv("OLLAMA_READ_TIMEOUT_SECONDS", "30")
    OLLAMA_MAX_RESPONSE_BYTES = os.getenv(
        "OLLAMA_MAX_RESPONSE_BYTES", "1048576"
    )


def get_database_connect_args(ca_path: str | None = None):
    """Build MySQL TLS connection arguments for Aiven configured via env."""
    ca_path = ca_path if ca_path is not None else os.getenv("AIVEN_CA_PATH", "")
    if not ca_path:
        return {}
    return {"ssl": {"ca": ca_path}}
