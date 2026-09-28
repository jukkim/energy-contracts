from copy import deepcopy
import importlib.util
from pathlib import Path

import jsonschema
import pytest
from energy_contracts import load_schema
from energy_contracts._utils.resource_authorization import evaluate, policy


@pytest.mark.parametrize("role", list(policy()["roles"]))
@pytest.mark.parametrize("action", ["read:asset", "analyze:asset"])
def test_roles_only_access_current_assignment(role, action):
    common = dict(role=role, action=action, verified=True, assigned_asset_ids=["AIR-A"])
    assert evaluate(asset_ids=["AIR-A"], **common) == (True, "AUTHORIZED")
    assert evaluate(asset_ids=["AIR-B"], **common) == (False, "AIROS_TARGET_NOT_ASSIGNED")
    assert evaluate(asset_ids=["AIR-A", "AIR-B"], **common)[0] is False


@pytest.mark.parametrize("role", list(policy()["roles"]))
def test_assignment_never_implies_dispatch(role):
    assert evaluate(role=role, action="exec:dispatch", asset_ids=["AIR-A"],
                    assigned_asset_ids=["AIR-A"], verified=True, action_kind="LED") == (
                        False, "AUTHORIZATION_CONDITIONS_UNDEFINED")


SAVINGS_CODES = sorted(load_schema("measure_cost_catalog")["default"]["measures"])


@pytest.mark.parametrize("kind", SAVINGS_CODES)
def test_portfolio_manager_approves_savings_measure_on_assigned_asset(kind):
    # 2026-09-28 user decision: allowed side.
    assert evaluate(role="portfolio_manager", action="approve:action", asset_ids=["AIR-A"],
                    assigned_asset_ids=["AIR-A"], verified=True, action_kind=kind) == (True, "AUTHORIZED")


def test_approval_denied_outside_scope():
    ok = dict(role="portfolio_manager", action="approve:action", asset_ids=["AIR-A"],
              assigned_asset_ids=["AIR-A"], verified=True, action_kind="LED")
    assert evaluate(**ok) == (True, "AUTHORIZED")
    for change, reason in [
            ({"asset_ids": ["AIR-B"]}, "AIROS_TARGET_NOT_ASSIGNED"),
            ({"asset_ids": ["AIR-A", "AIR-B"]}, "AIROS_TARGET_NOT_ASSIGNED"),
            ({"action_kind": None}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action_kind": "setpoint_change"}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action_kind": "equipment_shutdown"}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action_kind": "contract_change"}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action_kind": "M07"}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action_kind": "led"}, "AUTHORIZATION_ACTION_KIND_DENIED"),
            ({"action": "exec:dispatch"}, "AUTHORIZATION_CONDITIONS_UNDEFINED"),
            ({"verified": False}, "AUTHORIZATION_IDENTITY_REQUIRED")]:
        assert evaluate(**dict(ok, **change)) == (False, reason), change
    for role in set(policy()["roles"]) - {"portfolio_manager"}:
        assert evaluate(**dict(ok, role=role)) == (False, "AUTHORIZATION_ACTION_DENIED"), role


def test_approval_rule_is_invisible_to_consumers_that_cannot_evaluate_conditions():
    rules = policy()
    rule = rules["actions"]["approve:action"]
    # Consumers that only know `allow_with_assignment` (AIROS context filter,
    # AgentLeague `action in permissions`) must see a non-allow effect.
    assert rule["effect"] == "allow_with_assignment_and_conditions"
    assert rule["grants_execution"] is False and rules["execution_authorized"] is False
    old_consumer_permissions = [p for p in rules["roles"]["portfolio_manager"]["permissions"]
                                if rules["actions"][p]["effect"] == "allow_with_assignment"]
    assert "approve:action" not in old_consumer_permissions
    assert rule["reason_code"] == "AUTHORIZATION_CONDITIONS_UNEVALUATED"


def test_unknown_or_empty_condition_denies(monkeypatch):
    from energy_contracts._utils import resource_authorization as ra
    ok = dict(role="portfolio_manager", action="approve:action", asset_ids=["AIR-A"],
              assigned_asset_ids=["AIR-A"], verified=True, action_kind="LED")
    base = policy()
    for conditions in [{"action_kind": base["actions"]["approve:action"]["conditions"]["action_kind"],
                        "max_cost_krw": {"limit": 1}}, {}, None,
                       {"action_kind": {"vocabulary_ref": "measure_cost_catalog.json#/default/measures",
                                        "match": "prefix"}}]:
        patched = deepcopy(base)
        patched["actions"]["approve:action"]["conditions"] = conditions
        monkeypatch.setattr(ra, "policy", lambda patched=patched: patched)
        assert ra.evaluate(**ok) == (False, "AUTHORIZATION_CONDITIONS_UNEVALUATED"), conditions
    monkeypatch.setattr(ra, "policy", lambda: base)
    assert ra.evaluate(**ok) == (True, "AUTHORIZED")


def test_auth_scopes_default_validates_against_its_action_rule_schema():
    schema = load_schema("auth_scopes")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(schema["default"], schema)
    bad = deepcopy(schema["default"])
    bad["resource_authorization"]["actions"]["approve:action"]["conditions"]["max_cost_krw"] = {}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    bad = deepcopy(schema["default"])
    bad["resource_authorization"]["actions"]["approve:action"]["grants_execution"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    bad = deepcopy(schema["default"])
    del bad["resource_authorization"]["actions"]["approve:action"]["conditions"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_unknown_roles_actions_and_declarations_cannot_grant_access():
    common = dict(role="portfolio_manager", action="read:asset", asset_ids=["AIR-A"],
                  assigned_asset_ids=["AIR-A"], verified=True)
    for change, reason in [({"role": "admin"}, "AUTHORIZATION_ROLE_UNKNOWN"),
                           ({"action": "delete:asset"}, "AUTHORIZATION_ACTION_UNKNOWN"),
                           ({"verified": False}, "AUTHORIZATION_IDENTITY_REQUIRED"),
                           ({"verified": "true"}, "AUTHORIZATION_IDENTITY_REQUIRED"),
                           ({"asset_ids": []}, "AUTHORIZATION_TARGET_REQUIRED"),
                           ({"asset_ids": ["*"]}, "AUTHORIZATION_TARGET_REQUIRED"),
                           ({"assigned_asset_ids": ["*"]}, "AIROS_TARGET_NOT_ASSIGNED")]:
        assert evaluate(**dict(common, **change)) == (False, reason)


def test_contract_receipt_rejects_fake_allow_execution_and_secret_fields():
    schema = load_schema("resource_authorization")
    jsonschema.Draft202012Validator.check_schema(schema)
    receipt = dict(schema="airo-authorization-decision/v1", login_id="manager.1",
                   role="portfolio_manager", action="read:asset", asset_ids=["AIR-A"],
                   allowed=True, reason_code="AUTHORIZED", assignment_revision="a" * 64,
                   policy_version="1.0", policy_sha256="b" * 64, execution_authorized=False)
    jsonschema.validate(receipt, schema)
    for change in [{"execution_authorized": True}, {"asset_ids": []},
                   {"reason_code": "AIROS_TARGET_NOT_ASSIGNED"}, {"token": "secret"}]:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(dict(receipt, **change), schema)
    jsonschema.validate(dict(receipt, action="unknown:action", allowed=False,
                             reason_code="AUTHORIZATION_ACTION_UNKNOWN"), schema)


def test_role_namespace_does_not_inherit_global_admin():
    common = load_schema("auth_scopes")
    assert "portfolio_manager" not in common["default"]["scopes"]
    for role in policy()["roles"].values():
        assert role["inherits"] == []
        assert {"read:asset", "analyze:asset"} <= set(role["permissions"])
    approvers = {name for name, role in policy()["roles"].items() if "approve:action" in role["permissions"]}
    assert approvers == {"portfolio_manager"}
    assert not any("exec:dispatch" in role["permissions"] for role in policy()["roles"].values())


def test_generated_python_and_typescript_export_policy_from_schema():
    import sys
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "scripts"))
    import gen_constants as gen
    schemas = gen.load_schemas()
    code = gen.gen_python(schemas)
    namespace = {}
    exec(code, namespace)
    assert namespace["AUTH_RESOURCE_AUTHORIZATION"] == policy()
    assert "export const AUTH_RESOURCE_AUTHORIZATION = " in gen.gen_typescript(schemas)


@pytest.mark.parametrize("action", ["write:home_consent", "revoke:home_consent", "write:home_protection"])
def test_household_choices_require_owner_current_assignment_and_home_class(action):
    args = dict(role="home_owner", action=action, asset_ids=["AIR-HOM-001"], assigned_asset_ids=["AIR-HOM-001"], verified=True, asset_classes={"AIR-HOM-001": "HOM"})
    assert evaluate(**args) == (True, "AUTHORIZED")
    assert evaluate(**dict(args, role="platform_admin"))[0] is False
    assert evaluate(**dict(args, assigned_asset_ids=[]))[0] is False
    assert evaluate(**dict(args, asset_classes={}))[1] == "AUTHORIZATION_RESOURCE_CLASS_DENIED"
    assert evaluate(**dict(args, asset_classes={"AIR-HOM-001": "BLD"}))[0] is False


def test_metadata_admin_write_still_requires_own_assignment():
    args = dict(role="platform_admin", action="write:asset_record", asset_ids=["AIR-DRW-001"], assigned_asset_ids=["AIR-DRW-001"], verified=True)
    assert evaluate(**args) == (True, "AUTHORIZED")
    assert evaluate(**dict(args, role="portfolio_manager"))[0] is False
    assert evaluate(**dict(args, assigned_asset_ids=[]))[0] is False
