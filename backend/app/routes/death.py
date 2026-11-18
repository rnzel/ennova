# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP death-trigger boundary
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.domain.accounts import AccountRole
from app.routes.common import (
    account_or_remote_key,
    bearer_required,
    current_account,
    json_body,
    limiter,
)

death_bp = Blueprint("death", __name__)
CONFIRMATION = "I CONFIRM DEATH TRIGGER"


@death_bp.post("/death-trigger")
@bearer_required(AccountRole.OWNER)
@limiter.limit("5 per minute", key_func=account_or_remote_key)
def trigger():
    account = current_account()
    state = current_app.extensions["api_state"]
    if state.is_triggered(account.owner_id):
        return jsonify({"death_triggered": True, "policy_frozen": True}), 200
    body = json_body()
    auth = current_app.extensions["auth_service"]
    auth.verify_trigger(
        account,
        body.get("password", ""),
        body.get("confirmation", ""),
        CONFIRMATION,
    )
    state.trigger(account.owner_id)
    state.add_audit(
        current_app.extensions["audit_record"](
            account.account_id, account.owner_id, "death_trigger",
            "accepted", current_app.extensions["clock"]()
        )
    )
    return jsonify({"death_triggered": True, "policy_frozen": True}), 200
