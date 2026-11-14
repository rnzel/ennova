# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Language design / immutable abstract syntax tree
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class Selector:
    """Marker base class for policy selectors."""

    __slots__ = ()


class ProtocolStatement:
    """Marker base class for statements scoped to a protocol block."""

    __slots__ = ()

class TopLevelStatement:
    """Marker base class for policy statements outside protocol blocks."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class MentioningSelector(Selector):
    """Select entries mentioning a named person identifier."""

    name: str


@dataclass(frozen=True, slots=True)
class TaggedSelector(Selector):
    """Select entries bearing a quoted topic tag."""

    tag: str


@dataclass(frozen=True, slots=True)
class MaySeeExistence(ProtocolStatement):
    """Grant existence-level access to a selector."""

    selector: Selector


@dataclass(frozen=True, slots=True)
class MayRead(ProtocolStatement):
    """Grant summary- or verbatim-level access to a selector."""

    level: str
    selector: Selector


@dataclass(frozen=True, slots=True)
class MayNotSeeExistence(ProtocolStatement):
    """Deny existence-level access to a selector."""

    selector: Selector


@dataclass(frozen=True, slots=True)
class MayNotRead(ProtocolStatement):
    """Deny summary- or verbatim-level access to a selector."""

    level: str
    selector: Selector


@dataclass(frozen=True, slots=True)
class ProtocolBlock(TopLevelStatement):
    """A beneficiary protocol and its ordered grant/deny statements."""

    person: str
    statements: tuple[ProtocolStatement, ...]

    def __post_init__(self) -> None:
        """Ensure protocol statements are stored in an immutable tuple."""
        if not isinstance(self.statements, tuple):
            raise TypeError("protocol statements must be a tuple.")


@dataclass(frozen=True, slots=True)
class ReleaseLetter(TopLevelStatement):
    """A letter release rule for one person and a calendar release date."""

    title: str
    person: str
    release_date: date


@dataclass(frozen=True, slots=True)
class Trustee(TopLevelStatement):
    """The optional top-level trustee identity."""

    person: str


@dataclass(frozen=True, slots=True)
class TransferCustody(TopLevelStatement):
    """A custody transfer rule triggered by trustee unavailability."""

    person: str
    unavailable_days: int


@dataclass(frozen=True, slots=True)
class DefaultWritingMode(TopLevelStatement):
    """The default writing mode named by the policy."""

    mode: str


@dataclass(frozen=True, slots=True)
class Policy:
    """An immutable policy preserving top-level source order."""

    statements: tuple[TopLevelStatement, ...]

    def __post_init__(self) -> None:
        """Ensure top-level statements are stored in an immutable tuple."""
        if not isinstance(self.statements, tuple):
            raise TypeError("policy statements must be a tuple.")
