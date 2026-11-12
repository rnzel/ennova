# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Object-oriented diary model
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum


class AccessLevel(str, Enum):
    """Data label for a grant's requested access level; it does not authorize access."""

    EXISTENCE = "existence"
    SUMMARY = "summary"
    VERBATIM = "verbatim"


def _require_nonempty(value: str, field_name: str) -> str:
    """Validate a required string and return it without changing its value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


class Entry(ABC):
    """Base class for an original diary or letter entry."""

    __slots__ = ("_entry_id", "_created_at", "_original_content")

    def __init__(
        self, entry_id: str, created_at: datetime, original_content: str
    ) -> None:
        """Create an entry using explicit identity, timestamp, and original content."""
        self._entry_id = _require_nonempty(entry_id, "entry_id")
        if not isinstance(created_at, datetime):
            raise TypeError("created_at must be a datetime.")
        if not isinstance(original_content, str):
            raise TypeError("original_content must be a string.")
        self._created_at = created_at
        self._original_content = original_content

    @property
    def entry_id(self) -> str:
        """Return the stable entry identifier."""
        return self._entry_id

    @property
    def created_at(self) -> datetime:
        """Return the caller-supplied creation timestamp."""
        return self._created_at

    @property
    def original_content(self) -> str:
        """Return the preserved original text."""
        return self._original_content

    @property
    @abstractmethod
    def kind(self) -> str:
        """Return the concrete entry kind."""


class DiaryEntry(Entry):
    """An original diary entry."""

    __slots__ = ()

    @property
    def kind(self) -> str:
        """Identify this entry as a diary entry."""
        return "diary"


class LetterEntry(Entry):
    """An original letter entry with recipient and release metadata."""

    __slots__ = ("_title", "_recipient", "_release_date")

    def __init__(
        self,
        entry_id: str,
        created_at: datetime,
        original_content: str,
        title: str,
        recipient: str,
        release_date: date | None = None,
    ) -> None:
        """Create a letter with explicit recipient and optional release date."""
        super().__init__(entry_id, created_at, original_content)
        self._title = _require_nonempty(title, "title")
        self._recipient = _require_nonempty(recipient, "recipient")
        if release_date is not None and (
            not isinstance(release_date, date) or isinstance(release_date, datetime)
        ):
            raise TypeError("release_date must be a date or None.")
        self._release_date = release_date

    @property
    def title(self) -> str:
        """Return the letter title."""
        return self._title

    @property
    def recipient(self) -> str:
        """Return the intended recipient."""
        return self._recipient

    @property
    def release_date(self) -> date | None:
        """Return the optional release date."""
        return self._release_date

    @property
    def kind(self) -> str:
        """Identify this entry as a letter."""
        return "letter"


class Vault:
    """Append-only in-memory container for diary entries."""

    __slots__ = ("_entries", "_entry_ids")

    def __init__(self) -> None:
        """Create an empty vault."""
        self._entries: list[Entry] = []
        self._entry_ids: set[str] = set()

    def append(self, entry: Entry) -> None:
        """Append an entry once, rejecting duplicate identifiers."""
        if not isinstance(entry, Entry):
            raise TypeError("entry must be an Entry.")
        if entry.entry_id in self._entry_ids:
            raise ValueError(f"Entry ID already exists: {entry.entry_id}")
        self._entries.append(entry)
        self._entry_ids.add(entry.entry_id)

    def get(self, entry_id: str) -> Entry | None:
        """Return the entry with this identifier, or None if absent."""
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    @property
    def entries(self) -> tuple[Entry, ...]:
        """Return an immutable snapshot in append order."""
        return tuple(self._entries)


class Beneficiary:
    """A person recorded as a beneficiary, without implicit access rights."""

    __slots__ = ("_beneficiary_id", "_name")

    def __init__(self, beneficiary_id: str, name: str) -> None:
        """Create a beneficiary identity."""
        self._beneficiary_id = _require_nonempty(beneficiary_id, "beneficiary_id")
        self._name = _require_nonempty(name, "name")

    @property
    def beneficiary_id(self) -> str:
        """Return the beneficiary identifier."""
        return self._beneficiary_id

    @property
    def name(self) -> str:
        """Return the beneficiary name."""
        return self._name


class Grant:
    """Policy data describing an intended grant; it does not make access decisions."""

    __slots__ = ("_beneficiary_id", "_selector", "_access_level")

    def __init__(
        self, beneficiary_id: str, selector: str, access_level: AccessLevel
    ) -> None:
        """Create a grant description for a beneficiary and selector."""
        self._beneficiary_id = _require_nonempty(beneficiary_id, "beneficiary_id")
        self._selector = _require_nonempty(selector, "selector")
        if not isinstance(access_level, AccessLevel):
            raise TypeError("access_level must be an AccessLevel.")
        self._access_level = access_level

    @property
    def beneficiary_id(self) -> str:
        """Return the beneficiary identifier referenced by this grant."""
        return self._beneficiary_id

    @property
    def selector(self) -> str:
        """Return the policy selector represented by this grant."""
        return self._selector

    @property
    def access_level(self) -> AccessLevel:
        """Return the requested access level without evaluating it."""
        return self._access_level


class Protocol:
    """Encapsulated collection of policy grant data, not an access evaluator."""

    __slots__ = ("_grants",)

    def __init__(self) -> None:
        """Create an empty protocol."""
        self._grants: list[Grant] = []

    def add_grant(self, grant: Grant) -> None:
        """Add a grant description to the protocol."""
        if not isinstance(grant, Grant):
            raise TypeError("grant must be a Grant.")
        self._grants.append(grant)

    @property
    def grants(self) -> tuple[Grant, ...]:
        """Return an immutable snapshot of the protocol's grants."""
        return tuple(self._grants)


class Owner:
    """The diary owner and the owner of their vault and protocol."""

    __slots__ = ("_owner_id", "_name", "_vault", "_protocol")

    def __init__(self, owner_id: str, name: str) -> None:
        """Create an owner with a new empty vault and protocol."""
        self._owner_id = _require_nonempty(owner_id, "owner_id")
        self._name = _require_nonempty(name, "name")
        self._vault = Vault()
        self._protocol = Protocol()

    @property
    def owner_id(self) -> str:
        """Return the owner identifier."""
        return self._owner_id

    @property
    def name(self) -> str:
        """Return the owner's name."""
        return self._name

    @property
    def vault(self) -> Vault:
        """Return the owner's append-only vault."""
        return self._vault

    @property
    def protocol(self) -> Protocol:
        """Return the owner's policy-data protocol."""
        return self._protocol
