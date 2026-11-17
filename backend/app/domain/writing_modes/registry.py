# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented writing-mode registry and policy resolution
from __future__ import annotations

from collections.abc import Callable

from app.errors import UnknownWritingMode
from app.policy import DefaultWritingMode, Policy

from .modes import LightFix, Review, Verbatim, WritingMode

_ModeFactory = Callable[[], WritingMode]
_REGISTRY: dict[str, _ModeFactory] = {
    "verbatim": Verbatim,
    "light_fix": LightFix,
    "review": Review,
}


def get_writing_mode(name: str) -> WritingMode:
    """Build a registered mode or raise a typed unknown-mode error."""
    if not isinstance(name, str) or not name.strip():
        raise UnknownWritingMode({"name": name})
    factory = _REGISTRY.get(name.casefold())
    if factory is None:
        raise UnknownWritingMode({"name": name})
    return factory()


def resolve_writing_mode(policy: Policy) -> tuple[WritingMode, bool]:
    """Resolve the last policy default, falling back to Verbatim safely."""
    if not isinstance(policy, Policy):
        raise TypeError("policy must be a Policy.")
    defaults = tuple(
        statement
        for statement in policy.statements
        if isinstance(statement, DefaultWritingMode)
    )
    if not defaults:
        return Verbatim(), True
    try:
        return get_writing_mode(defaults[-1].mode), False
    except UnknownWritingMode:
        return Verbatim(), True
