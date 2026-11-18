# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting authentication orchestration over a repository
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import unicodedata
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from app.domain.accounts import (
    AccountRole,
    Invitation,
    UserAccount,
    UserRepository,
)
from app.errors import AuthenticationError, InvalidBeneficiaryError
from app.policy.lexer import POLICY_IDENT_RE, POLICY_RESERVED_WORDS

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 64
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128
JWT_LIFETIME = timedelta(minutes=5)
MAX_OUTSTANDING_INVITATIONS = 10
LOGIN_DELAY_BASE_SECONDS = 1
LOGIN_DELAY_MAX_SECONDS = 8
_DUMMY_PASSWORD_HASH = generate_password_hash(
    "ennova-dummy-password-that-is-never-accepted"
)
_DUMMY_INVITATION_HASH = hashlib.sha256(
    b"ennova-dummy-invitation-that-is-never-accepted"
).hexdigest()


def normalize_username(username: str) -> str:
    """NFKC-normalize, trim, and casefold a username."""
    if not isinstance(username, str):
        raise TypeError("username must be a string.")
    normalized = unicodedata.normalize("NFKC", username).strip().casefold()
    if not USERNAME_MIN_LENGTH <= len(normalized) <= USERNAME_MAX_LENGTH:
        raise ValueError("username length is invalid.")
    if any(not (char.isalnum() or char in "_-.") for char in normalized):
        raise ValueError("username contains an invalid character.")
    return normalized


def normalize_password(password: str) -> str:
    """NFKC-normalize a password while preserving intentional spaces."""
    if not isinstance(password, str):
        raise TypeError("password must be a string.")
    normalized = unicodedata.normalize("NFKC", password)
    if not PASSWORD_MIN_LENGTH <= len(normalized) <= PASSWORD_MAX_LENGTH:
        raise ValueError("password length is invalid.")
    return normalized


def normalize_person_id(person_id: str) -> str:
    """Validate a policy identifier and return its lowercase form."""
    if not isinstance(person_id, str):
        raise TypeError("person_id must be a string.")
    normalized = unicodedata.normalize("NFKC", person_id).strip().casefold()
    if not POLICY_IDENT_RE.fullmatch(normalized):
        raise ValueError("person_id must match the policy identifier pattern.")
    if normalized in POLICY_RESERVED_WORDS:
        raise ValueError("person_id is reserved by the policy language.")
    return normalized


class AuthService:
    """Register accounts, redeem invitations, and issue fail-closed JWTs."""

    def __init__(
        self,
        repository: UserRepository,
        *,
        clock: Callable[[], datetime] | None = None,
        jwt_secret: str | None = None,
        jwt_lifetime: timedelta = JWT_LIFETIME,
    ) -> None:
        """Create authentication orchestration with injectable time and secret."""
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._jwt_secret = (
            jwt_secret if jwt_secret is not None else os.getenv("JWT_SECRET_KEY")
        )
        self._jwt_lifetime = jwt_lifetime
        self._login_failures: dict[str, tuple[int, datetime]] = {}

    def register_owner(self, username: str, password: str) -> UserAccount:
        """Register an owner; the registration path fixes the role."""
        normalized_username = normalize_username(username)
        normalized_password = normalize_password(password)
        self._reject_username_password_match(
            normalized_username, normalized_password
        )
        account_id = secrets.token_urlsafe(24)
        account = UserAccount(
            account_id,
            normalized_username,
            account_id,
            normalized_username,
            AccountRole.OWNER,
            generate_password_hash(normalized_password),
        )
        self._repository.add_user(account)
        return account

    def create_invitation(
        self, owner_id: str, person_id: str, expires_at: datetime
    ) -> str:
        """Issue one hashed, owner-bound, expiring beneficiary invitation."""
        normalized_person_id = normalize_person_id(person_id)
        owner = self._repository.get_by_account_id(owner_id)
        if owner is None or owner.role is not AccountRole.OWNER:
            raise AuthenticationError({"reason": "owner_not_found"})
        if self._repository.get_by_person_id(owner_id, normalized_person_id):
            raise ValueError("person already registered.")
        now = self._now()
        if expires_at <= now:
            raise ValueError("expires_at must be in the future.")
        outstanding = sum(
            not invitation.used and invitation.expires_at > now
            for invitation in self._repository.list_invitations(owner_id)
        )
        if outstanding >= MAX_OUTSTANDING_INVITATIONS:
            raise ValueError("invitation limit reached.")
        code = secrets.token_urlsafe(32)
        self._repository.add_invitation(
            Invitation(
                self._hash_invitation(code),
                owner_id,
                normalized_person_id,
                expires_at,
            )
        )
        return code

    def register_beneficiary(
        self,
        owner_id: str,
        invitation_code: str,
        username: str,
        password: str,
    ) -> UserAccount:
        """Redeem an invitation using one generic failure for all invalid cases."""
        normalized_username = normalize_username(username)
        normalized_password = normalize_password(password)
        self._reject_username_password_match(
            normalized_username, normalized_password
        )
        presented_hash = self._hash_invitation(invitation_code)
        invitations = self._repository.list_invitations(owner_id)
        matched: Invitation | None = None
        for invitation in invitations:
            if hmac.compare_digest(invitation.code_hash, presented_hash):
                matched = invitation
        hmac.compare_digest(_DUMMY_INVITATION_HASH, presented_hash)
        now = self._now()
        owner = self._repository.get_by_account_id(owner_id)
        person_id = matched.person_id if matched is not None else ""
        already_registered = bool(
            person_id
            and self._repository.get_by_person_id(owner_id, person_id)
        )
        valid = bool(
            matched is not None
            and owner is not None
            and owner.role is AccountRole.OWNER
            and not matched.used
            and matched.expires_at > now
            and not already_registered
        )
        if not valid:
            raise InvalidBeneficiaryError({"reason": "invitation_rejected"})
        account_id = secrets.token_urlsafe(24)
        account = UserAccount(
            account_id,
            normalized_username,
            owner_id,
            person_id,
            AccountRole.BENEFICIARY,
            generate_password_hash(normalized_password),
        )
        self._repository.add_user(account)
        self._repository.mark_invitation_used(matched)
        return account

    def redeem_invitation(
        self, invitation_code: str, username: str, password: str
    ) -> UserAccount:
        """Redeem an invitation using only its stored owner and person IDs."""
        normalized_username = normalize_username(username)
        normalized_password = normalize_password(password)
        self._reject_username_password_match(
            normalized_username, normalized_password
        )
        presented_hash = self._hash_invitation(invitation_code)
        matched = self._repository.find_invitation(presented_hash)
        now = self._now()
        owner_id = matched.owner_id if matched is not None else ""
        owner = self._repository.get_by_account_id(owner_id)
        person_id = matched.person_id if matched is not None else ""
        already_registered = bool(
            person_id
            and self._repository.get_by_person_id(owner_id, person_id)
        )
        password_hash = generate_password_hash(normalized_password)
        valid = bool(
            matched is not None
            and owner is not None
            and owner.role is AccountRole.OWNER
            and not matched.used
            and matched.expires_at > now
            and not already_registered
        )
        if not valid:
            raise InvalidBeneficiaryError({"reason": "invitation_rejected"})
        account_id = secrets.token_urlsafe(24)
        account = UserAccount(
            account_id,
            normalized_username,
            owner_id,
            person_id,
            AccountRole.BENEFICIARY,
            password_hash,
        )
        self._repository.add_user(account)
        self._repository.mark_invitation_used(matched)
        return account

    def login(self, username: str, password: str) -> str:
        """Authenticate with an escalating-delay, generic failure path."""
        normalized_username = normalize_username(username)
        normalized_password = normalize_password(password)
        now = self._now()
        account = self._repository.get_by_username(normalized_username)
        failures, available_at = self._login_failures.get(
            normalized_username, (0, now)
        )
        password_hash = account.password_hash if account else _DUMMY_PASSWORD_HASH
        password_matches = check_password_hash(password_hash, normalized_password)
        delayed = now < available_at
        if delayed or not password_matches or account is None:
            next_failures = failures + 1
            delay = min(
                LOGIN_DELAY_BASE_SECONDS * (2 ** (next_failures - 1)),
                LOGIN_DELAY_MAX_SECONDS,
            )
            self._login_failures[normalized_username] = (
                next_failures,
                now + timedelta(seconds=delay),
            )
            raise AuthenticationError({"reason": "login_rejected"})
        self._login_failures.pop(normalized_username, None)
        return self._issue_token(account, now)

    def account_from_token(self, token: str) -> UserAccount:
        """Decode a token and re-read the account identified by opaque ``sub``."""
        secret = self._require_secret()
        try:
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={
                    "require": ["exp", "iat", "sub"],
                    "verify_exp": False,
                    "verify_iat": False,
                },
            )
        except (jwt.InvalidTokenError, TypeError, ValueError) as error:
            raise AuthenticationError({"reason": "token_rejected"}) from error
        account_id = claims.get("sub")
        issued_at = claims.get("iat")
        expires_at = claims.get("exp")
        now = int(self._now().timestamp())
        if (
            not isinstance(account_id, str)
            or not isinstance(issued_at, int)
            or not isinstance(expires_at, int)
            or issued_at > now
            or expires_at <= now
        ):
            raise AuthenticationError({"reason": "token_subject_missing"})
        account = self._repository.get_by_account_id(account_id)
        if account is None:
            raise AuthenticationError({"reason": "account_missing"})
        return account

    def verify_trigger(
        self, account: UserAccount, password: str, phrase: str, expected: str
    ) -> None:
        """Verify trigger credentials with the same delay state as login."""
        now = self._now()
        failures, available_at = self._login_failures.get(
            account.username, (0, now)
        )
        try:
            normalized = normalize_password(password)
            password_matches = check_password_hash(
                account.password_hash, normalized
            )
        except (TypeError, ValueError):
            password_matches = False
        phrase_matches = (
            isinstance(phrase, str)
            and hmac.compare_digest(phrase, expected)
        )
        if now < available_at or not password_matches or not phrase_matches:
            next_failures = failures + 1
            delay = min(
                LOGIN_DELAY_BASE_SECONDS * (2 ** (next_failures - 1)),
                LOGIN_DELAY_MAX_SECONDS,
            )
            self._login_failures[account.username] = (
                next_failures,
                now + timedelta(seconds=delay),
            )
            raise AuthenticationError({"reason": "trigger_rejected"})
        self._login_failures.pop(account.username, None)

    def registered_person_ids(self, owner_id: str) -> tuple[str, ...]:
        """Return casefolded registered person IDs, never beneficiary usernames."""
        return tuple(
            account.person_id.casefold()
            for account in self._repository.list_for_owner(owner_id)
        )

    def _issue_token(self, account: UserAccount, now: datetime) -> str:
        secret = self._require_secret()
        issued_at = int(now.timestamp())
        payload = {
            "sub": account.account_id,
            "role": account.role.value,
            "owner_id": account.owner_id,
            "iat": issued_at,
            "exp": int((now + self._jwt_lifetime).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    def _require_secret(self) -> str:
        if not isinstance(self._jwt_secret, str) or len(
            self._jwt_secret.encode("utf-8")
        ) < 32:
            raise AuthenticationError({"reason": "jwt_secret_invalid"})
        return self._jwt_secret

    def _now(self) -> datetime:
        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise TypeError("clock must return an aware datetime.")
        return now

    @staticmethod
    def _hash_invitation(code: str) -> str:
        if not isinstance(code, str):
            code = ""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def _reject_username_password_match(
        username: str, password: str
    ) -> None:
        if hmac.compare_digest(username, password.casefold()):
            raise ValueError("password must not equal username.")
