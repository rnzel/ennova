"""Isolated SQL-backed account repository tests using temporary SQLite schemas."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect

from app import create_app
from app.domain.accounts import (
    AccountRole, Invitation, UserAccount,
)
from app.errors import ConflictError
from app.extensions import db
from app.infrastructure.sql_user_repository import SQLAlchemyUserRepository
from app.models import AccountRecord, InvitationRecord
from app.services.auth_service import AuthService


@pytest.fixture
def persisted_app():
    app = create_app(config_overrides={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "JWT_SECRET_KEY": "p" * 32,
    }, user_repository=SQLAlchemyUserRepository())
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def account(account_id, username, email, *, owner_id=None, person_id=None, role=AccountRole.OWNER):
    return UserAccount(
        account_id, username, email, owner_id or account_id,
        person_id or username, role, "pbkdf2:sha256:hash-only",
    )


def test_sql_repository_persists_owner_and_login_after_new_repository_instance(persisted_app):
    with persisted_app.app_context():
        service = AuthService(SQLAlchemyUserRepository(), jwt_secret="p" * 32)
        owner = service.register_owner("Lola", "LOLA@example.com", "owner-password-123")
        first_hash = db.session.get(AccountRecord, owner.account_id).password_hash
        assert first_hash != "owner-password-123"

        reopened = AuthService(SQLAlchemyUserRepository(), jwt_secret="p" * 32)
        assert reopened.login("LOLA", "owner-password-123")
        assert reopened._repository.get_by_account_id(owner.account_id) == owner


def test_sql_repository_global_unique_username_and_email(persisted_app):
    with persisted_app.app_context():
        repo = SQLAlchemyUserRepository()
        repo.add_user(account("one", "same", "one@example.com"))
        with pytest.raises(ConflictError) as username:
            repo.add_user(account("two", "same", "two@example.com"))
        assert username.value.detail == {"field": "username"}
        with pytest.raises(ConflictError) as email:
            repo.add_user(account("three", "other", "one@example.com"))
        assert email.value.detail == {"field": "email"}


def test_beneficiary_and_invitation_commit_atomically(persisted_app):
    with persisted_app.app_context():
        repo = SQLAlchemyUserRepository()
        owner = account("owner", "owner", "owner@example.com")
        repo.add_user(owner)
        invitation = Invitation(
            "a" * 64, owner.account_id, "maria",
            datetime.now(timezone.utc) + timedelta(hours=1),
        )
        repo.add_invitation(invitation)
        beneficiary = account(
            "beneficiary", "taken", "beneficiary@example.com",
            owner_id=owner.account_id, person_id="maria", role=AccountRole.BENEFICIARY,
        )
        repo.add_user(beneficiary, invitation)
        assert repo.find_invitation(invitation.code_hash).used
        assert repo.get_by_person_id(owner.account_id, "maria") == beneficiary


def test_failed_beneficiary_insert_rolls_back_invitation_consumption(persisted_app):
    with persisted_app.app_context():
        repo = SQLAlchemyUserRepository()
        owner = account("owner", "owner", "owner@example.com")
        repo.add_user(owner)
        repo.add_user(account("existing", "taken", "existing@example.com"))
        invitation = Invitation(
            "b" * 64, owner.account_id, "maria",
            datetime.now(timezone.utc) + timedelta(hours=1),
        )
        repo.add_invitation(invitation)
        beneficiary = account(
            "beneficiary", "taken", "new@example.com",
            owner_id=owner.account_id, person_id="maria", role=AccountRole.BENEFICIARY,
        )
        with pytest.raises(ConflictError):
            repo.add_user(beneficiary, invitation)
        assert not repo.find_invitation(invitation.code_hash).used
        assert db.session.get(AccountRecord, "beneficiary") is None


def test_database_connection_error_is_not_replaced_by_memory_repository():
    with pytest.raises(RuntimeError, match="MySQL DATABASE_URL"):
        create_app(config_overrides={"TESTING": False, "SQLALCHEMY_DATABASE_URI": None})


def test_persistence_tables_have_database_level_unique_constraints(persisted_app):
    with persisted_app.app_context():
        account_constraints = inspect(db.engine).get_unique_constraints("accounts")
        names = {constraint["name"] for constraint in account_constraints}
        assert {"uq_accounts_username", "uq_accounts_email", "uq_accounts_owner_person"} <= names
        assert "invitations" in inspect(db.engine).get_table_names()
