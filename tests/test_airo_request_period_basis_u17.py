"""airo_request 2.8(2026-10-15 U17): Period.basis += prior_answer_relative — 이어 묻기가 앞 답의 기간에서 옮긴 상대 달.

반례 양쪽: 새 값 받음 · 2.7 의 값 그대로 받음 · 목록 밖 값은 여전히 거절 · pydantic 모델이 같은 값을 안다."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas" / "airo_request.json"


def _period_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sub = {"$defs": schema["$defs"], "$ref": "#/$defs/Period"}
    return Draft202012Validator(sub)


def _ok(basis) -> bool:
    inst = {"start": "2026-07-01T00:00:00+09:00", "end_exclusive": "2026-08-01T00:00:00+09:00", "basis": basis}
    return not list(_period_validator().iter_errors(inst))


def test_prior_answer_relative_is_accepted_and_old_values_still_are():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["version"] == "2.8"
    assert _ok("prior_answer_relative")
    for old in ("question_literal", "calendar_relative_to_today", "coverage_of_needs", "forecast_relative_to_today", None):
        assert _ok(old), old


def test_unknown_basis_is_still_rejected():
    assert not _ok("prior_answer")
    assert not _ok("relative_to_prior")


def test_pydantic_models_know_the_new_basis():
    from energy_contracts._pydantic_models import airo_request, airo_result
    assert any(m.value == "prior_answer_relative" for m in airo_request.Basis) if hasattr(airo_request, "Basis") else True
    assert "prior_answer_relative" in Path(airo_request.__file__).read_text(encoding="utf-8")
    assert "prior_answer_relative" in Path(airo_result.__file__).read_text(encoding="utf-8")


def test_basis_enum_only_appended_against_the_0108_tag():
    """반대쪽: v0.3.108(2.7) 의 basis 목록이 새 목록의 **앞부분 그대로**이고 더한 것은 prior_answer_relative 하나 · 나머지 스키마는 가산만."""
    import pytest
    import importlib.util
    spec = importlib.util.spec_from_file_location("_t0372", Path(__file__).with_name("test_declared_assumptions_0372.py"))
    t0372 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t0372)
    strict_additive, _at_tag = t0372.strict_additive, t0372._at_tag
    old = _at_tag("v0.3.108", "airo_request.json")
    if old is None:
        pytest.skip("[해당 없음] git 태그 v0.3.108 을 못 읽었다 — 통과가 아니다(못 잼)")
    new = json.loads(SCHEMA.read_text(encoding="utf-8"))
    before = [v for v in old["$defs"]["Period"]["properties"]["basis"]["enum"]]
    after = [v for v in new["$defs"]["Period"]["properties"]["basis"]["enum"]]
    assert [v for v in after if v not in before] == ["prior_answer_relative"]
    assert [v for v in after if v != "prior_answer_relative"] == before          # 순서·값 그대로(null 포함)
    problems, checked = strict_additive(old, new, "", {"/version", "/updated", "/$comment",
                                                         "/$defs/Period/properties/basis/enum",
                                                         "/$defs/Period/properties/basis/description"}, "airo_request.json")
    assert not problems, problems
    assert checked >= 200, checked
