# -*- coding: utf-8 -*-
"""0.3.62 초안(RV-B, 2026-09-29) — airo_request 2.4 · airo_result 1.1 · interface_types 1.1 · declared_assumptions 1.2.

게이트웨이가 실제로 싣는 모양을 선언했다(가산). 항목마다 반례 양쪽 — 받아야 할 것 · 막아야 할 것. 검사 N 건을 단언한다.
작성만(묶음 끝 한 번 실행).
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
    resources = []
    for fp in sorted(SCHEMAS.glob("*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        resources.append((data.get("$id") or BASE + fp.name,
                          Resource.from_contents(data, default_specification=referencing.jsonschema.DRAFT202012)))
    assert resources, "0 schemas loaded - that is a failure, not a pass"
    return Registry().with_resources(resources)


def _v(name: str, ref: str = "") -> Draft202012Validator:
    return Draft202012Validator({"$ref": f"{BASE}{name}{ref}"}, registry=_registry())


def _ok(v, inst) -> bool:
    return not list(v.iter_errors(inst))


def test_versions_bumped_for_the_draft():
    assert _load("airo_request.json")["version"] == "2.4"
    assert _load("airo_result.json")["version"] == "1.1"
    # 근거(2026-09-29 3b-2 S1, 0.3.63 초안): interface_types 는 RequestResolution 추가로 1.1 → 1.2 (스키마 $comment 1.2 절).
    # 1.1 의 가산분(QuantityUnit += score)은 아래 test_declared_units_are_quantity_units_and_new_entries_exist 가 그대로
    # 지키고, 1.2 가산분은 RequestResolution 이 $defs 에 있는지로 본다(반대쪽). 나머지 세 판 고정은 바꾸지 않는다.
    assert "RequestResolution" in _load("interface_types.json")["$defs"]
    assert _load("interface_types.json")["version"] == "1.2"
    assert _load("declared_assumptions.json")["version"] == "1.2"
    for name in ("airo_request.json", "airo_result.json", "interface_types.json", "declared_assumptions.json"):
        Draft202012Validator.check_schema(_load(name))


# ── TargetContext 2.4 ─────────────────────────────────────────────────────────────────────────────────────────
def test_target_context_resolved_and_unresolved_forms():
    v = _v("airo_request.json", "#/$defs/TargetContext")
    resolved = {"contract": "airo-target-context/v1", "kind": "portfolio", "ids": ["AIR-PRT-001"],
                "source": "login_assignment", "resolved": True, "choices": ["AIR-PRT-001"],
                "chain_steps": ["store_cohort_rank"], "final_target_source": "chain_step"}
    unresolved = {"contract": "airo-target-context/v1", "kind": None, "ids": [], "source": None, "resolved": False}
    assert _ok(v, resolved) and _ok(v, unresolved)
    old_valid = {"kind": "region", "ids": ["region:11680"], "source": "query"}      # 2.3 에서 유효 → 2.4 에서도
    assert _ok(v, old_valid)
    for bad in ({**resolved, "source": "request"}, {**resolved, "kind": "building_group"},
                {**resolved, "final_target_source": "step_result"}, {**resolved, "contract": "other/v1"},
                {**unresolved, "ids": ["x"]}, {**unresolved, "resolved": True},
                {**old_valid, "ids": []}, {**resolved, "period": None}):
        assert not _ok(v, bad), bad


# ── Period 2.4 ────────────────────────────────────────────────────────────────────────────────────────────────
def test_period_source_and_reasons():
    v = _v("airo_request.json", "#/$defs/Period")
    good = {"contract": "airo-period/v1", "text": "2025년 7월", "start": "2025-07-01T00:00:00+09:00",
            "end_exclusive": "2025-08-01T00:00:00+09:00", "tz": "Asia/Seoul", "grain": "month",
            "basis": "question_literal", "source": "query", "basis_ko": "질문의 날짜 표현",
            "generator": "serving/general_ops/periods.py"}
    unresolved = {"basis": None, "source": None, "why": "질문에 기간이 없다", "contract": "airo-period/v1"}
    forecast = {**good, "basis": "forecast_relative_to_today"}
    assert _ok(v, good) and _ok(v, unresolved) and _ok(v, forecast)
    for bad in ({**good, "source": "question"}, {**good, "basis": "made_up"}, {**good, "extra": 1},
                {**good, "contract": "airo-period/v2"}):
        assert not _ok(v, bad), bad


# ── Continuation 2.4 · tool_input_mode · as_of ────────────────────────────────────────────────────────────────
def test_continuation_needs_a_tool_or_a_prior_request():
    v = _v("airo_request.json", "#/$defs/Continuation")
    assert _ok(v, {"requested_tool": "region_energy_aggregate"})               # 2.3 모양 그대로
    assert _ok(v, {"prior_request_id": "STUDIO-ASK-1"})                        # 2.4: 되묻기 답의 둘째 턴
    assert _ok(v, {"requested_tool": "x", "tool_arguments": {}, "prior_request_id": "R"})
    assert not _ok(v, {})
    assert not _ok(v, {"tool_arguments": {"a": 1}})
    assert not _ok(v, {"prior_request_id": ""})


def test_envelope_tool_input_mode_and_as_of():
    v = _v("airo_request.json")
    base = {"asker": {"login_id": "demo.policy.001"}, "query": "강남구 사용량"}
    assert _ok(v, base)
    assert _ok(v, {**base, "tool_input_mode": "evidence-bound-v1"}) and _ok(v, {**base, "tool_input_mode": "literal-v1"})
    assert not _ok(v, {**base, "tool_input_mode": "free-text"})
    assert _ok(v, {**base, "as_of": "2025-08-15"}) and _ok(v, {**base, "as_of": "2025-08-15T09:00:00+09:00"})
    assert not _ok(v, {**base, "as_of": "어제"})
    assert not _ok(v, {**base, "intent": "plan"})                               # 2.3 규칙 그대로(계획은 이어가기 필수)


def test_unspecified_archetype_target_is_the_all_marker_only():
    v = _v("airo_request.json", "#/$defs/Target")
    assert _ok(v, {"kind": "archetype", "ids": ["archetype:all"]})
    assert _ok(v, {"kind": "archetype", "ids": ["archetype:B01_Office"], "archetype": {"building_type": "B01"}})
    assert not _ok(v, {"kind": "archetype", "ids": ["archetype:B01_Office"]})   # 특정 원형이면 archetype 필수


# ── airo_result 1.1 ToolCall · ToolResult ──────────────────────────────────────────────────────────────────────
def test_tool_call_and_result_shapes_both_sides():
    call = _v("airo_result.json", "#/$defs/ToolCall")
    res = _v("airo_result.json", "#/$defs/ToolResult")
    assert _ok(call, {"name": "t", "arguments": {}}) and _ok(call, {"name": "t", "arguments": {}, "step_id": "s",
                                                                    "member": "AIR-RET-001"})
    assert not _ok(call, {"tool": "t", "arguments": {}}) and not _ok(call, {"name": "t"})
    assert _ok(res, {"tool": "t", "result": {}}) and _ok(res, {"tool": "t", "rejected_result": {"type": "x", "issues": []}})
    assert not _ok(res, {"name": "t", "result": {}}) and not _ok(res, {"tool": "t"})
    assert not _ok(res, {"tool": "t", "result": {}, "rejected_result": {"type": "x", "issues": []}})


# ── declared_assumptions 1.2 · QuantityUnit 1.1 ───────────────────────────────────────────────────────────────
def test_declared_units_are_quantity_units_and_new_entries_exist():
    units = set(_load("interface_types.json")["$defs"]["QuantityUnit"]["enum"])
    d = _load("declared_assumptions.json")["default"]
    used = {spec["unit"] for spec in d.values() if isinstance(spec, dict) and "unit" in spec}
    assert used and used <= units, used - units
    assert "score" in units and "%" not in units
    for key in ("scenario_vacancy_default", "switchable_cut_share_default", "control_priority_default",
                "assumption_search_ranges", "ranked_rows_top_n_default"):
        assert d[key]["classification"] == "assumed" and d[key]["source"], key
    assert list(d["assumption_search_ranges"]["ranges"]) == ["energy_price_multiplier", "savings_realization",
                                                              "capex_multiplier", "discount_rate", "lifetime_multiplier"]
    assert d["top_share_pct_default"]["unit"] == "pct"
