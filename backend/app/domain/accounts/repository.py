# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Object-oriented repository abstraction
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Invitation, UserAccount


class UserRepository(ABC):
    """Storage interface used by authentication without database coupling."""

    @abstractmethod
    def add_user(self, account: UserAccount) -> None:
        """Store an account, rejecting duplicate normalized identities."""

    @abstractmethod
    def get_by_username(self, username: str) -> UserAccount | None:
        """Find an account by its normalized username."""

    @abstractmethod
    def get_by_account_id(self, account_id: str) -> UserAccount | None:
        """Find an account by its opaque account identifier."""

    @abstractmethod
    def get_by_person_id(self, owner_id: str, person_id: str) -> UserAccount | None:
        """Find an account already registered for an owner/person pair."""

    @abstractmethod
    def list_for_owner(self, owner_id: str) -> tuple[UserAccount, ...]:
        """Return accounts registered under one owner."""

    @abstractmethod
    def add_invitation(self, invitation: Invitation) -> None:
        """Store an invitation."""

    @abstractmethod
    def list_invitations(self, owner_id: str) -> tuple[Invitation, ...]:
        """Return all invitations issued by one owner."""

    @abstractmethod
    def mark_invitation_used(self, invitation: Invitation) -> None:
        """Mark one stored invitation as redeemed."""


class InMemoryUserRepository(UserRepository):
    """Small append-only account and invitation repository for domain tests."""

    def __init__(self) -> None:
        """Create empty account and invitation indexes."""
        self._accounts: dict[str, UserAccount] = {}
        self._usernames: dict[str, UserAccount] = {}
        self._owner_people: dict[tuple[str, str], UserAccount] = {}
        self._invitations: list[Invitation] = []

    def add_user(self, account: UserAccount) -> None:
        """Store an account with unique username and owner/person identity."""
        if account.username in self._usernames:
            raise ValueError("username already exists")
        if (account.owner_id, account.person_id) in self._owner_people:
            raise ValueError("person already registered")
        self._accounts[account.account_id] = account
        self._usernames[account.username] = account
        self._owner_people[(account.owner_id, account.person_id)] = account

    def get_by_username(self, username: str) -> UserAccount | None:
        """Find an account by normalized username."""
        return self._usernames.get(username)

    def get_by_account_id(self, account_id: str) -> UserAccount | None:
        """Find an account by opaque account identifier."""
        return self._accounts.get(account_id)

    def get_by_person_id(self, owner_id: str, person_id: str) -> UserAccount | None:
        """Find an account by owner and casefolded person identity."""
        return self._owner_people.get((owner_id, person_id))

    def list_for_owner(self, owner_id: str) -> tuple[UserAccount, ...]:
        """Return all accounts associated with an owner."""
        return tuple(
            account for account in self._accounts.values() if account.owner_id == owner_id
        )

    def add_invitation(self, invitation: Invitation) -> None:
        """Append an invitation record."""
        self._invitations.append(invitation)

    def list_invitations(self, owner_id: str) -> tuple[Invitation, ...]:
        """Return all invitations for an owner."""
        return tuple(
            invitation
            for invitation in self._invitations
            if invitation.owner_id == owner_id
        )

    def mark_invitation_used(self, invitation: Invitation) -> None:
        """Replace one invitation with its single-use redeemed state."""
        for index, current in enumerate(self._invitations):
            if current == invitation:
                self._invitations[index] = Invitation(
                    current.code_hash,
                    current.owner_id,
                    current.person_id,
                    current.expires_at,
                    used=True,
                )
                return
        raise ValueError("invitation not found")
