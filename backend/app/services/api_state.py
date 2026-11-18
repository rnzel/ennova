# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Back End; Roldan Jr. Bazares – Front End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented in-memory API state
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.policy import Policy


@dataclass(frozen=True, slots=True)
class PolicyVersion:
    """One accepted immutable policy version."""

    version: int
    source: str
    policy: Policy
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """An audit event that intentionally contains no sensitive text."""

    actor_id: str
    owner_id: str
    action: str
    status: str
    created_at: datetime
    resource_id: str | None = None


class InMemoryApiState:
    """Per-application policy, trigger, and audit state."""

    def __init__(self) -> None:
        self._policies: dict[str, list[PolicyVersion]] = {}
        self._triggered: set[str] = set()
        self._audits: list[AuditRecord] = []

    def active_policy(self, owner_id: str) -> PolicyVersion | None:
        versions = self._policies.get(owner_id, ())
        return versions[-1] if versions else None

    def accept_policy(
        self, owner_id: str, source: str, policy: Policy, created_at: datetime
    ) -> PolicyVersion:
        version = PolicyVersion(
            len(self._policies.get(owner_id, ())) + 1,
            source,
            policy,
            created_at,
        )
        self._policies.setdefault(owner_id, []).append(version)
        return version

    def is_triggered(self, owner_id: str) -> bool:
        return owner_id in self._triggered

    def trigger(self, owner_id: str) -> None:
        self._triggered.add(owner_id)

    def add_audit(self, record: AuditRecord) -> None:
        self._audits.append(record)

    def audits(self) -> tuple[AuditRecord, ...]:
        return tuple(self._audits)
