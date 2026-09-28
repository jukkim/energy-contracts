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


@pytest.mark.parametrize("action", ["approve:action", "exec:dispatch"])
def test_assignment_never_implies_approval_or_dispatch(action):
    assert evaluate(role="platform_admin", action=action, asset_ids=["AIR-A"],
                    assigned_asset_ids=["AIR-A"], verified=True) == (
                        False, "AUTHORIZATION_CONDITIONS_UNDEFINED")


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
