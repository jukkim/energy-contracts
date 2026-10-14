# -*- coding: utf-8 -*-
"""airo_request 2.7(2026-10-14 묶음 U1): 봉투 최상위 선택 칸 ``presentation{mode: auto|none}``.

근거 = 캠페인 ``docs/NL_TO_BE3D_UNIFICATION_PLAN_2026-10-14.md`` §3.2·§10(표시 선호를 분석 의도와 분리 · 생략 = 기존 동작).
반례 양쪽 — 받아야 할 것 · 막아야 할 것. 검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator  # noqa: E402

SCHEMA = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas" / "airo_request.json"
BASE = {"contract": "airo-request/v2", "surface": "studio",
        "asker": {"login_id": "demo.policy.001"}, "query": "강남구의 지난달 전력 사용량이 큰 건물을 비교해줘"}

_spec = importlib.util.spec_from_file_location("_t0372", Path(__file__).with_name("test_declared_assumptions_0372.py"))
_t0372 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t0372)
strict_additive, _at_tag = _t0372.strict_additive, _t0372._at_tag

#: 태그와 달라도 되는 자리 — 판 표지뿐(presentation 은 새 키라 strict_additive 가 그대로 받는다)
ALLOWED_CHANGES = {"/version", "/updated", "/$comment"}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _ok(inst) -> bool:
    return not list(Draft202012Validator(_schema()).iter_errors(inst))


def test_presentation_is_optional_and_accepts_both_modes():
    schema = _schema()
    assert schema["version"] == "2.7"
    Draft202012Validator.check_schema(schema)
    assert "presentation" not in schema["required"]
    accept = [BASE,                                                  # 생략 = 기존 봉투 그대로
              {**BASE, "presentation": {"mode": "auto"}},
              {**BASE, "presentation": {"mode": "none"}},
              {**BASE, "intent": "value", "presentation": {"mode": "auto"}}]
    assert len(accept) == 4
    for envelope in accept:
        assert _ok(envelope), envelope


def test_presentation_rejects_unknown_shapes():
    reject = [{**BASE, "presentation": {}},                          # mode 없음
              {**BASE, "presentation": {"mode": "map"}},             # 목록 밖(map/panel 은 응답 칸이다)
              {**BASE, "presentation": {"mode": "AUTO"}},
              {**BASE, "presentation": {"mode": None}},
              {**BASE, "presentation": {"mode": "auto", "scene": True}},   # 안쪽 모르는 칸
              {**BASE, "presentation": "auto"},
              {**BASE, "presentation": None},
              {**BASE, "presentations": {"mode": "auto"}}]           # 최상위 모르는 칸은 여전히 거절
    assert len(reject) == 8
    for envelope in reject:
        assert not _ok(envelope), envelope


def test_additive_against_the_0107_tag():
    old = _at_tag("v0.3.107", "airo_request.json")
    if old is None:
        pytest.skip("[해당 없음] git 태그 v0.3.107 을 못 읽었다 — 통과가 아니다(못 잼)")
    problems, checked = strict_additive(old, _schema(), "", ALLOWED_CHANGES, "airo_request.json")
    assert not problems, problems
    assert "presentation" not in old["properties"]
    assert checked >= 200, checked


def test_generated_model_knows_presentation():
    from energy_contracts._pydantic_models import airo_request as model
    assert [m.value for m in model.Mode] == _schema()["properties"]["presentation"]["properties"]["mode"]["enum"]
    with pytest.raises(Exception):
        model.Presentation(mode="auto", scene=True)
    assert model.Presentation(mode="none").mode.value == "none"
