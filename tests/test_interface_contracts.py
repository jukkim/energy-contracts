"""M3 interface standard (2026-09-29): airo-request/v2 2.3, interface_types, airo-result/v1, Refusal.

These tests read the modules and schemas themselves; nothing is counted with regular expressions.
Each gate is checked both ways (what it must block, and what it must let through), and every
test asserts that it actually checked something. Zero checks counts as a failure.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")
from jsonschema import Draft202012Validator  # noqa: E402
from referencing import Registry, Resource  # noqa: E402

SCHEMAS = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas"
BASE = "energy-contracts/"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _registry() -> Registry:
    """Load every EC schema into one registry, keyed by `$id` (the way consumers should read cross-file refs)."""
    resources = []
    for fp in sorted(SCHEMAS.glob("*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        uri = data.get("$id") or BASE + fp.name
        resources.append((uri, Resource.from_contents(data, default_specification=referencing.jsonschema.DRAFT202012)))
    assert resources, "0 schemas loaded - that is a failure, not a pass"
    return Registry().with_resources(resources)


def _validator(name: str, ref: str | None = None) -> Draft202012Validator:
    schema = {"$ref": f"{BASE}{name}{ref or ''}"}
    return Draft202012Validator(schema, registry=_registry())


def _ok(v: Draft202012Validator, inst) -> bool:
    return not list(v.iter_errors(inst))


NEW_OR_CHANGED = ["airo_request.json", "airo_result.json", "interface_types.json",
                  "error_response.json", "declared_assumptions.json"]


@pytest.mark.parametrize("name", NEW_OR_CHANGED)
def test_schema_is_valid_draft_2020_12(name):
    Draft202012Validator.check_schema(_load(name))


def test_airo_request_stays_single_file():
    """The gateway validates airo_request.json on its own (serving/airo_request_v2). A cross-file $ref would break it."""
    refs: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("$ref"), str):
                refs.append(node["$ref"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(_load("airo_request.json"))
    assert refs, "0 $ref found - the walk did not run"
    assert [r for r in refs if not r.startswith("#")] == []


def test_asset_kind_is_the_common_list():
    """AssetKind in the request envelope must match common.json AirAssetKind (it cannot $ref it, see above)."""
    request = _load("airo_request.json")["$defs"]["AssetKind"]["enum"]
    common = _load("common.json")["$defs"]["AirAssetKind"]["enum"]
    assert request and request == common


def test_quantity_units_cover_energy_base_units():
    units = set(_load("interface_types.json")["$defs"]["QuantityUnit"]["enum"])
    base = set(_load("energy_units.json")["default"]["base_units"].values())
    assert base, "0 base units read"
    assert base <= units, sorted(base - units)


def test_request_envelope_2_3_both_ways():
    v = Draft202012Validator(_load("airo_request.json"))
    asker = {"login_id": "demo.portfolio.001"}
    accept = [
        {"asker": asker, "query": "q", "target": {"kind": "asset", "ids": ["AIR-RET-0001"]}},  # 2.2 envelope unchanged
        {"asker": asker, "query": "q"},  # (1) target omitted
        {"asker": asker, "query": "q", "continuation": {"requested_tool": "t", "tool_arguments": {},
                                                        "prior_request_id": "R-1"}},  # (2)
        {"asker": asker, "query": "q", "intent": "plan", "continuation": {"requested_tool": "t"}},  # (3)
        {"asker": asker, "query": "q", "intent": "debate"},  # (4)
        {"asker": asker, "query": "q", "target": {"kind": "asset", "ids": ["AIR-RET-0001"], "asset_kind": "RET",
                                                  "members": [], "expansion": {"rule_id": "none"}}},
        {"asker": asker, "query": "q", "period": {"basis": "coverage_of_needs"}},
    ]
    reject = [
        {"asker": asker},  # query is still required
        {"query": "q"},  # asker is still required
        {"asker": asker, "query": "q", "intent": "plan"},  # plan without continuation
        {"asker": asker, "query": "q", "continuation": {"tool_arguments": {}}},  # no requested_tool
        {"asker": asker, "query": "q", "intent": "chat"},
        {"asker": asker, "query": "q", "target": {"kind": "portfolio", "ids": ["AIR-PRT-001"], "asset_kind": "RET"}},
        {"asker": asker, "query": "q", "target": {"kind": "asset", "ids": ["AIR-BLD-001"], "asset_kind": "PRT"}},
    ]
    assert len(accept) == 7 and len(reject) == 7
    assert [i for i, x in enumerate(accept) if not _ok(v, x)] == []
    assert [i for i, x in enumerate(reject) if _ok(v, x)] == []


def _result(**over):
    base = {"contract": "airo-result/v1", "status": "ok", "row_kind": "ranked",
            "target_context": {"kind": "asset", "ids": ["AIR-RET-0001"], "source": "query", "asset_kind": "RET"},
            "period_used": {"start": "2025-07-01T00:00:00+09:00", "end_exclusive": "2025-08-01T00:00:00+09:00",
                            "basis": "coverage_of_needs"},
            "columns": [{"name": "eui", "concept": "eui_kwh_m2", "unit": "kWh/m2", "classification": "measured"}],
            "rows": [{"eui": 210.0}],
            "population": {"row_count_full": 12, "rows_returned": 1, "truncated": True, "top_n_applied": 1},
            "absences": [], "classification": {"word": "measured"},
            "assumptions": [{"key": "top_share_pct_default", "value": 25.0, "unit": "%", "classification": "assumed",
                             "basis": "energy-contracts/declared_assumptions#top_share_pct_default"}],
            "ec_version": "0.3.61", "result_hash": "0123456789abcdef"}
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}


def test_result_envelope_both_ways():
    v = _validator("airo_result.json")
    refusal = {"code": "PLACE_AMBIGUOUS", "kind": "question", "field": "place", "message_ko": "m", "retry": "ask"}
    accept = [
        _result(),
        _result(status="refused", row_kind=None, columns=None, target_context=None, population=None,
                rows=[], classification={"word": "unknown"}, refusal=refusal),
        _result(row_kind="table", rows=[], population={"row_count_full": 0, "rows_returned": 0}),
        _result(row_kind="scalar", rows=[], population=None, summary={"total_kwh": 1.0}),
    ]
    reject = [
        _result(status="refused", refusal=None),  # a refusal status must carry the refusal
        _result(refusal=refusal),  # ok must not carry a refusal
        _result(row_kind="table", rows=[], population=None),  # an empty ok table must say it checked 0 rows
        _result(population=None),  # ranked needs population (top_n)
        _result(classification={"word": "measured_ish"}),  # not one of the 17 words
        _result(absences=[{"slot": "eui", "absence_kind": "absent"}]),
        _result(target_context=None),
    ]
    assert len(accept) == 4 and len(reject) == 7
    assert [i for i, x in enumerate(accept) if not _ok(v, x)] == []
    assert [i for i, x in enumerate(reject) if _ok(v, x)] == []


def test_problem_extension_is_additive_both_ways():
    v = Draft202012Validator(_load("error_response.json")["$defs"]["Problem"] | {"$defs": _load("error_response.json")["$defs"]})
    old = {"type": "https://errors.building-energy.xyz/v1/x", "title": "t", "status": 422, "code": "VALIDATION_FAILED"}
    new = old | {"kind": "question", "field": "target", "expected": ["asset"], "got": "parcel",
                 "message_ko": "m", "next_ko": "n", "retry": "ask", "legacy_code": "TARGET_REQUIRED"}
    assert _ok(v, old) and _ok(v, new)
    assert not _ok(v, old | {"kind": "other"})
    assert not _ok(v, old | {"retry": "maybe"})


def test_top_share_default_is_declared_assumed():
    spec = _load("declared_assumptions.json")["default"]["top_share_pct_default"]
    assert spec["value"] == 25.0 and spec["classification"] == "assumed" and spec["source"]
