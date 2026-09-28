"""Pure assignment/capability intersection; callers supply server-verified snapshots.

No token authentication, portfolio expansion or physical device binding happens here.
The caller must establish those facts before calling this function.
"""
from __future__ import annotations

from energy_contracts import load_schema


def policy() -> dict:
    return load_schema("auth_scopes")["default"]["resource_authorization"]


ALLOW = "allow_with_assignment"
ALLOW_IF = "allow_with_assignment_and_conditions"


def _vocabulary(ref: str) -> set[str]:
    """Resolve `<schema>.json#/json/pointer` to the keys of that mapping (match = key)."""
    name, _, pointer = ref.partition("#")
    node = load_schema(name.removesuffix(".json"))
    for part in [p for p in pointer.split("/") if p]:
        node = node[part]
    if not isinstance(node, dict) or not node:
        raise ValueError(f"vocabulary {ref} is not a non-empty mapping")
    return set(node)


def allowed_action_kinds(spec: dict) -> frozenset[str]:
    """The one place the allowed kinds are assembled: vocabulary keys + additional_kinds."""
    extra = spec.get("additional_kinds", [])
    if (spec.get("match") != "key" or not isinstance(spec.get("vocabulary_ref"), str)
            or not isinstance(extra, list) or not all(isinstance(k, str) and k for k in extra)):
        raise ValueError("unevaluable action_kind condition")
    return frozenset(_vocabulary(spec["vocabulary_ref"]) | set(extra))


def _condition_action_kind(spec: dict, action_kind: object) -> str | None:
    try:
        allowed = allowed_action_kinds(spec)
    except (ValueError, KeyError, TypeError):
        return "AUTHORIZATION_CONDITIONS_UNEVALUATED"
    if not isinstance(action_kind, str) or action_kind not in allowed:
        return "AUTHORIZATION_ACTION_KIND_DENIED"
    return None


# The only conditions this module can evaluate; any other key denies (never skipped).
CONDITION_EVALUATORS = {"action_kind": _condition_action_kind}


def evaluate(*, role: str, action: str, asset_ids: list[str],
             assigned_asset_ids: list[str], verified: bool,
             asset_classes: dict[str, str] | None = None,
             action_kind: str | None = None) -> tuple[bool, str]:
    """Deny by default; no global administrator inheritance or wildcard expansion.

    `action_kind` is the requested action's code, checked only by rules whose effect is
    `allow_with_assignment_and_conditions` (e.g. approve:action = savings measure code).
    """
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
    if rule["effect"] not in (ALLOW, ALLOW_IF):
        return False, rule.get("reason_code", "AUTHORIZATION_ACTION_DENIED")
    required_class = rule.get("required_asset_class")
    if required_class and any((asset_classes or {}).get(aid) != required_class for aid in asset_ids):
        return False, "AUTHORIZATION_RESOURCE_CLASS_DENIED"
    if action not in rules["roles"][role]["permissions"]:
        return False, "AUTHORIZATION_ACTION_DENIED"
    if rule["effect"] == ALLOW_IF:
        conditions = rule.get("conditions")
        if not isinstance(conditions, dict) or not conditions:
            return False, "AUTHORIZATION_CONDITIONS_UNEVALUATED"
        for key, spec in conditions.items():
            check = CONDITION_EVALUATORS.get(key)
            if check is None or not isinstance(spec, dict):
                return False, "AUTHORIZATION_CONDITIONS_UNEVALUATED"
            reason = check(spec, action_kind)
            if reason:
                return False, reason
    return True, "AUTHORIZED"
