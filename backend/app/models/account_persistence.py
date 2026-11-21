"""Relational storage for accounts and single-use beneficiary invitations."""

from __future__ import annotations

from app.extensions import db


class AccountRecord(db.Model):
    __tablename__ = "accounts"
    __table_args__ = (
        db.UniqueConstraint("username", name="uq_accounts_username"),
        db.UniqueConstraint("email", name="uq_accounts_email"),
        db.UniqueConstraint("owner_id", "person_id", name="uq_accounts_owner_person"),
        db.Index("ix_accounts_owner_id", "owner_id"),
    )

    account_id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    owner_id = db.Column(db.String(64), nullable=False)
    person_id = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )


class InvitationRecord(db.Model):
    __tablename__ = "invitations"
    __table_args__ = (
        db.Index("ix_invitations_owner_id", "owner_id"),
    )

    code_hash = db.Column(db.String(64), primary_key=True)
    owner_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    person_id = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
