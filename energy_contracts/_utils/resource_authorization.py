"""Pure assignment/capability intersection; callers supply server-verified snapshots.

No token authentication, portfolio expansion or physical device binding happens here.
The caller must establish those facts before calling this function.
"""
from __future__ import annotations

from energy_contracts import load_schema


def policy() -> dict:
    return load_schema("auth_scopes")["default"]["resource_authorization"]


def evaluate(*, role: str, action: str, asset_ids: list[str],
             assigned_asset_ids: list[str], verified: bool,
             asset_classes: dict[str, str] | None = None) -> tuple[bool, str]:
    """Deny by default; no global administrator inheritance or wildcard expansion."""
    rules = policy()
    if verified is not True:
        return False, "AUTHORIZATION_IDENTITY_REQUIRED"
    if role not in rules["roles"]:
        return False, "AUTHORIZATION_ROLE_UNKNOWN"
    rule = rules["actions"].get(action)
    if rule is None:
        return False, "AUTHORIZATION_ACTION_UNKNOWN"
    if not asset_ids or not all(isinstance(x, str) and x and x != "*" for x in asset_ids):
        return False, "AUTHORIZATION_TARGET_REQUIRED"
    if not set(asset_ids).issubset(set(assigned_asset_ids)):
        return False, "AIROS_TARGET_NOT_ASSIGNED"
    if rule["effect"] != "allow_with_assignment":
        return False, rule.get("reason_code", "AUTHORIZATION_ACTION_DENIED")
    required_class = rule.get("required_asset_class")
    if required_class and any((asset_classes or {}).get(aid) != required_class for aid in asset_ids):
        return False, "AUTHORIZATION_RESOURCE_CLASS_DENIED"
    if action not in rules["roles"][role]["permissions"]:
        return False, "AUTHORIZATION_ACTION_DENIED"
    return True, "AUTHORIZED"
