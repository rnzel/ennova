# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jezelle Gabion – Documentator
# Paradigm: Object-oriented immutable account records
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AccountRole(str, Enum):
    """Registration-path role assigned by the authentication service."""

    OWNER = "owner"
    BENEFICIARY = "beneficiary"


@dataclass(frozen=True, slots=True)
class UserAccount:
    """Stored account identity with a hashed password."""

    account_id: str
    username: str
    owner_id: str
    person_id: str
    role: AccountRole
    password_hash: str


@dataclass(frozen=True, slots=True)
class Invitation:
    """Hashed, owner-bound, single-use beneficiary invitation."""

    code_hash: str
    owner_id: str
    person_id: str
    expires_at: datetime
    used: bool = False
