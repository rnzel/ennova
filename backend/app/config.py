# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Infrastructure / configuration
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///ennova.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AIVEN_CA_PATH = os.getenv("AIVEN_CA_PATH", "")
    SWIPL_EXECUTABLE = os.getenv("SWIPL_EXECUTABLE", "swipl")


def get_database_connect_args():
    """Build MySQL TLS connection arguments for Aiven configured via env."""
    ca_path = os.getenv("AIVEN_CA_PATH", "")
    if not ca_path:
        return {}
    return {"ssl": {"ca": ca_path}}
