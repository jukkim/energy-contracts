# -*- coding: utf-8 -*-
"""0.3.75(2026-10-01) — airo_request 2.6: surface enum 에 ``canvas``(energy-decision-canvas — 6단계 흐름도).

근거 = 화면 세션 요청(캠페인 ``scratch/capability_first/requests_round3.md`` 주 세션 메모 06:25 — 캔버스는 이미 ``surface: "canvas"`` 를
보내고, 2.5 봉투는 목록 밖 이름이라 422 로 거절했다). canvas 가 어떤 규칙을 따르는지(Studio 와 같은 선언 공무원 표면)는 게이트웨이
한 곳이 정한다 — 스키마는 이름만 받는다. 반례 양쪽 — 받아야 할 것 · 막아야 할 것. 검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "energy_contracts" / "schemas" / "airo_request.json"
BASE = {"asker": {"login_id": "demo.policy.001", "alias": "정책 담당 공무원", "persona": "P-GOV"},
        "query": "강남구 공공건물 에너지 사용량 상위 10곳을 보여줘"}
#: 캔버스 화면이 보내는 봉투 모양 그대로(energy-decision-canvas lib/query.ts buildEnvelope — 선언 공무원 · 기본 대상 강남구)
CANVAS = {**BASE, "contract": "airo-request/v2", "request_id": "canvas-mg0abc-1x2y3z4w", "surface": "canvas",
          "target": {"kind": "region", "ids": ["region:11680"], "label": "강남구", "source": "user_default"}}
#: 2.5 까지의 표면 이름(목록 순서 그대로) — 2.6 은 뒤에 canvas 하나만 붙였다
SURFACES_2_5 = ["mcp", "studio", "lab", "airos", "agentleague"]

_spec = importlib.util.spec_from_file_location("_t0372", Path(__file__).with_name("test_declared_assumptions_0372.py"))
_t0372 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t0372)
strict_additive, _at_tag = _t0372.strict_additive, _t0372._at_tag

#: 태그와 달라도 되는 자리 — 판 표지와 표면 목록(뒤에 붙이기만 — 아래에서 앞 원소를 따로 본다)
ALLOWED_CHANGES = {"/version", "/updated", "/$comment", "/properties/surface/enum"}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _ok(inst) -> bool:
    return not list(Draft202012Validator(_schema()).iter_errors(inst))


def test_canvas_is_one_more_surface_name_appended():
    schema = _schema()
    assert schema["version"] == "2.6"
    enum = schema["properties"]["surface"]["enum"]
    assert enum == [*SURFACES_2_5, "canvas"]              # 앞 다섯은 그대로, 순서도 그대로
    assert len(enum) == len(set(enum))
    Draft202012Validator.check_schema(schema)


def test_canvas_envelopes_are_accepted():
    accept = [CANVAS,
              {**BASE, "surface": "canvas"},
              {**CANVAS, "intent": "both"},
              {**CANVAS, "interpretation": {"frame_id": "Q-SET", "from_request_id": "canvas-mg0abc-prev"}},
              {k: v for k, v in CANVAS.items() if k != "target"}]            # 2.3 대상 생략도 canvas 로
    assert len(accept) == 5
    for envelope in accept:
        assert _ok(envelope), envelope


def test_envelopes_valid_in_2_5_stay_valid():
    accept = [BASE, *({**BASE, "surface": s} for s in SURFACES_2_5),
              {**BASE, "intent": "both", "surface": "studio", "tool_input_mode": "literal-v1"}]
    assert len(accept) == 7
    for envelope in accept:
        assert _ok(envelope), envelope


def test_unknown_surface_names_are_still_rejected():
    reject = [{**BASE, "surface": "Canvas"},              # 대소문자
              {**BASE, "surface": "canvas "},             # 뒤 공백
              {**BASE, "surface": " canvas"},
              {**BASE, "surface": "CANVAS"},
              {**BASE, "surface": "canva"},
              {**BASE, "surface": "energy-decision-canvas"},  # 앱 폴더 이름은 표면 이름이 아니다
              {**BASE, "surface": "canvas\n"},
              {**BASE, "surface": "studio2"},
              {**BASE, "surface": "be3d"},
              {**BASE, "surface": ""},
              {**BASE, "surface": None},
              {**BASE, "surface": ["canvas"]},
              {**BASE, "surface": 1},
              {**CANVAS, "surfaces": "canvas"}]           # 최상위의 모르는 칸은 여전히 거절
    assert len(reject) == 14
    for envelope in reject:
        assert not _ok(envelope), envelope


def test_additive_against_the_0374_tag():
    old = _at_tag("v0.3.74", "airo_request.json")
    if old is None:
        pytest.skip("[해당 없음] git 태그 v0.3.74 를 못 읽었다 — 통과가 아니다(못 잼)")
    problems, checked = strict_additive(old, _schema(), "", ALLOWED_CHANGES, "airo_request.json")
    assert not problems, problems
    before = old["properties"]["surface"]["enum"]
    assert before == SURFACES_2_5
    assert _schema()["properties"]["surface"]["enum"][:len(before)] == before        # 뒤에 붙이기만
    assert checked >= 200, checked                       # 문서 잎 전부(0 건이면 그것이 사고다)


def test_generated_model_knows_canvas_and_only_the_listed_names():
    from energy_contracts._pydantic_models import airo_request as model
    assert [s.value for s in model.Surface] == _schema()["properties"]["surface"]["enum"]
    assert model.Surface("canvas").value == "canvas"
    for bad in ("Canvas", "canvas ", "studio2"):
        with pytest.raises(ValueError):
            model.Surface(bad)
