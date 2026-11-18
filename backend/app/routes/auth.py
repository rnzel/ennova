# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP authentication routes
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify

from app.domain.accounts import AccountRole
from app.routes.common import bearer_required, current_account, json_body, limiter

auth_bp = Blueprint("auth", __name__)


def _account_payload(account):
    return {
        "account_id": account.account_id,
        "username": account.username,
        "owner_id": account.owner_id,
        "person_id": account.person_id,
        "role": account.role.value,
    }


@auth_bp.post("/auth/register-owner")
@limiter.limit("3 per hour")
def register_owner():
    body = json_body()
    account = current_app.extensions["auth_service"].register_owner(
        body["username"], body["password"]
    )
    return jsonify(_account_payload(account)), 201


@auth_bp.post("/auth/login")
@limiter.limit("5 per minute")
def login():
    body = json_body()
    token = current_app.extensions["auth_service"].login(
        body["username"], body["password"]
    )
    return jsonify({"access_token": token, "token_type": "Bearer"}), 200


@auth_bp.post("/auth/register-beneficiary")
@limiter.limit("3 per hour")
def register_beneficiary():
    body = json_body()
    account = current_app.extensions["auth_service"].redeem_invitation(
        body["invitation_code"], body["username"], body["password"]
    )
    return jsonify(_account_payload(account)), 201


@auth_bp.post("/invitations")
@bearer_required(AccountRole.OWNER)
def create_invitation():
    account = current_account()
    service = current_app.extensions["auth_service"]
    if current_app.extensions["api_state"].is_triggered(account.owner_id):
        raise PermissionError("operation unavailable")
    body = json_body()
    expires_at = datetime.fromisoformat(body["expires_at"].replace("Z", "+00:00"))
    code = service.create_invitation(
        account.owner_id, body["person_id"], expires_at
    )
    return jsonify(
        {
            "invitation_code": code,
            "person_id": body["person_id"].casefold(),
            "expires_at": expires_at.isoformat(),
        }
    ), 201
