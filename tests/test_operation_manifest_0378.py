# -*- coding: utf-8 -*-
"""0.3.78(2026-10-01) — operation_manifest 0.2: 등록된 연산마다 요구 자료 선언을 채운다(G4 · 가산).

근거 = 캠페인 ``docs/ACCEPTANCE_INSPECTION_PLAN_2026-10-01.md`` §3 G4('새 기능 = 기능 계약 한 곳 등록') · ``docs/GENERALIZATION_PLAN_2026-09-28.md``
§6.2 P0(정본 기본 ``operations={}``). 내용은 게이트웨이 생성기(``8.simulation/ems_transformer/tools/gen_operation_manifest.py``)가 능력표에서 파생한다.
반례 양쪽 — 받아야 할 항목 · 막아야 할 항목. 검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "energy_contracts" / "schemas" / "operation_manifest.json"
FIELDS_01 = {"needs", "criteria", "day_window", "default_period", "assumptions", "absence_when_missing"}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _op_validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator({**schema["$defs"]["Operation"], "$defs": schema["$defs"]})


def test_default_validates_and_is_not_empty():
    schema = _schema()
    default = schema["default"]
    Draft202012Validator(schema).validate(default)
    ops = default["operations"]
    assert len(ops) == default["operation_count"] > 0          # 빈 표를 '선언 완료'로 세지 않는다
    checked = 0
    validator = _op_validator(schema)
    vocabulary = default["needs_vocabulary"]
    for key, entry in ops.items():
        assert not list(validator.iter_errors(entry)), key
        assert key == (entry["tool"] if entry["operation"] is None else f"{entry['tool']}/{entry['operation']}")
        assert all(n in vocabulary or (n.startswith("channel:") and len(n) > 8) for n in entry["needs"]), key
        checked += 1
    assert checked == len(ops) > 0


@pytest.mark.parametrize("mutate", [
    lambda e: e.pop("needs"),                                   # 요구 자료 없음
    lambda e: e.update(needs=[]),                               # 빈 요구 자료
    lambda e: e.update(default_period="last_month"),            # 기간 규칙 어휘 밖
    lambda e: e.update(subject_kinds=["store"]),                # 대상 종류 어휘 밖
    lambda e: e.update(registered_when="sometimes"),
    lambda e: e.update(unknown_field=1),                        # 칸 이름 오타
])
def test_bad_entries_are_rejected(mutate):
    schema = _schema()
    entry = copy.deepcopy(next(iter(schema["default"]["operations"].values())))
    mutate(entry)
    assert list(_op_validator(schema).iter_errors(entry))


def test_good_minimal_entries_are_accepted():
    schema = _schema()
    validator = _op_validator(schema)
    for entry in ({"needs": ["channel:energy"], "default_period": "coverage_of_needs"},
                  {"needs": ["simulation_pack"], "default_period": "not_applicable", "tool": "t", "operation": None},
                  {"needs": ["subject_data_not_derived"], "default_period": "tool_rule", "registered_when": "question_forms_on"}):
        assert not list(validator.iter_errors(entry))


def test_unknown_need_is_named_not_counted_as_absent():
    vocabulary = _schema()["default"]["needs_vocabulary"]
    assert "subject_data_not_derived" in vocabulary and "못 잼" in vocabulary["subject_data_not_derived"]
    assert "arguments_only" not in vocabulary                    # 모르는 것을 '자료 없이 계산'으로 적지 않는다


def test_v01_fields_are_kept():
    """가산만 — 0.1 의 Operation 칸·필수·기간 낱말이 그대로 있다(v0.3.77 태그와 맞댄다)."""
    # 2026-10-01: CI 체크아웃은 태그를 가져오지 않아 `git show v0.3.77:…` 이 실패했다 — v0.3.77 판 스키마를 고정 사본으로 둔다
    #   (사본 = `git show v0.3.77:energy_contracts/schemas/operation_manifest.json` 그대로 · 비교 규칙은 바꾸지 않는다)
    old = json.loads((ROOT / "tests" / "fixtures" / "operation_manifest_schema_v0.3.77.json").read_text(encoding="utf-8"))
    new = _schema()
    old_op, new_op = old["$defs"]["Operation"], new["$defs"]["Operation"]
    assert set(old_op["properties"]) == FIELDS_01 <= set(new_op["properties"])
    assert old_op["required"] == new_op["required"]
    assert set(old_op["properties"]["default_period"]["enum"]) <= set(new_op["properties"]["default_period"]["enum"])
    assert old_op["additionalProperties"] is new_op["additionalProperties"] is False
