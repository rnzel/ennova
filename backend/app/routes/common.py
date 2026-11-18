# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP boundary
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import current_app, g, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.domain.accounts import AccountRole, UserAccount
from app.errors import AuthenticationError, EnnovaError

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def account_or_remote_key() -> str:
    """Key protected requests by account after authentication, else by address."""
    account = getattr(g, "account", None)
    if account is not None:
        return account.account_id
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.casefold() == "bearer" and token:
        try:
            account = current_app.extensions["auth_service"].account_from_token(
                token
            )
        except EnnovaError:
            account = None
        if account is not None:
            return account.account_id
    return get_remote_address()


def json_body() -> dict:
    """Require a JSON object request body."""
    if not request.is_json:
        raise ValueError("JSON is required.")
    value = request.get_json(silent=False)
    if not isinstance(value, dict):
        raise ValueError("JSON object is required.")
    return value


def bearer_required(role: AccountRole | None = None) -> Callable:
    """Require a Bearer JWT and re-read its account from the repository."""
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            scheme, _, token = header.partition(" ")
            if scheme.casefold() != "bearer" or not token:
                raise AuthenticationError({"reason": "authorization_missing"})
            service = current_app.extensions["auth_service"]
            account = service.account_from_token(token)
            if role is not None and account.role is not role:
                raise PermissionError("role denied")
            g.account = account
            return function(*args, **kwargs)
        return wrapped
    return decorator


def current_account() -> UserAccount:
    """Return the account set by bearer_required."""
    return g.account
