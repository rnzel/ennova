"""SQLAlchemy implementation of the account repository contract."""

from __future__ import annotations

from datetime import timezone

from sqlalchemy.exc import IntegrityError

from app.domain.accounts.models import AccountRole, Invitation, UserAccount
from app.errors import ConflictError, InvalidBeneficiaryError
from app.extensions import db
from app.models.account_persistence import AccountRecord, InvitationRecord

from app.domain.accounts.repository import UserRepository


def _aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _account(row):
    return UserAccount(
        row.account_id, row.username, row.email, row.owner_id, row.person_id,
        AccountRole(row.role), row.password_hash,
    )


def _invitation(row):
    return Invitation(
        row.code_hash, row.owner_id, row.person_id, _aware(row.expires_at), row.used
    )


def _utc_naive(value):
    """Store timezone-aware instants as UTC in MySQL's timezone-free DATETIME."""
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class SQLAlchemyUserRepository(UserRepository):
    """Persist accounts and invitations in the Flask application's database."""

    def add_user(self, account: UserAccount, invitation: Invitation | None = None) -> None:
        try:
            if invitation is not None:
                stored = db.session.get(
                    InvitationRecord, invitation.code_hash, with_for_update=True
                )
                if (
                    stored is None or stored.used
                    or stored.owner_id != invitation.owner_id
                    or stored.person_id != invitation.person_id
                    or _aware(stored.expires_at) != _aware(invitation.expires_at)
                ):
                    raise InvalidBeneficiaryError({"reason": "invitation_rejected"})
                stored.used = True
            db.session.add(AccountRecord(
                account_id=account.account_id, username=account.username,
                email=account.email, owner_id=account.owner_id,
                person_id=account.person_id, role=account.role.value,
                password_hash=account.password_hash,
            ))
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            message = " ".join(str(part) for part in getattr(error.orig, "args", ()))
            message = f"{message} {error.orig}"
            if "username" in message or "uq_accounts_username" in message:
                raise ConflictError({"field": "username"}) from None
            if "email" in message or "uq_accounts_email" in message:
                raise ConflictError({"field": "email"}) from None
            if "owner_person" in message or "uq_accounts_owner_person" in message:
                raise InvalidBeneficiaryError({"reason": "invitation_rejected"}) from None
            raise

    def get_by_username(self, username: str) -> UserAccount | None:
        row = db.session.execute(db.select(AccountRecord).where(AccountRecord.username == username)).scalar_one_or_none()
        return _account(row) if row else None

    def get_by_account_id(self, account_id: str) -> UserAccount | None:
        row = db.session.get(AccountRecord, account_id)
        return _account(row) if row else None

    def get_by_person_id(self, owner_id: str, person_id: str) -> UserAccount | None:
        row = db.session.execute(db.select(AccountRecord).where(
            AccountRecord.owner_id == owner_id, AccountRecord.person_id == person_id
        )).scalar_one_or_none()
        return _account(row) if row else None

    def list_for_owner(self, owner_id: str) -> tuple[UserAccount, ...]:
        rows = db.session.execute(db.select(AccountRecord).where(AccountRecord.owner_id == owner_id)).scalars()
        return tuple(_account(row) for row in rows)

    def add_invitation(self, invitation: Invitation) -> None:
        try:
            db.session.add(InvitationRecord(
                code_hash=invitation.code_hash, owner_id=invitation.owner_id,
                person_id=invitation.person_id, expires_at=_utc_naive(invitation.expires_at),
                used=invitation.used,
            ))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("invitation could not be stored") from None

    def list_invitations(self, owner_id: str) -> tuple[Invitation, ...]:
        rows = db.session.execute(db.select(InvitationRecord).where(InvitationRecord.owner_id == owner_id)).scalars()
        return tuple(_invitation(row) for row in rows)

    def find_invitation(self, code_hash: str) -> Invitation | None:
        row = db.session.get(InvitationRecord, code_hash)
        return _invitation(row) if row else None

    def mark_invitation_used(self, invitation: Invitation) -> None:
        row = db.session.get(InvitationRecord, invitation.code_hash, with_for_update=True)
        if row is None:
            raise ValueError("invitation not found")
        row.used = True
        db.session.commit()
