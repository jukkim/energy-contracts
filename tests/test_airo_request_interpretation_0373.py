# -*- coding: utf-8 -*-
"""0.3.73(2026-10-01) — airo_request 2.5: 봉투 최상위 선택 칸 ``interpretation{frame_id, from_request_id}``.

근거 = 캠페인 ``docs/CAPABILITY_FIRST_QUERY_DESIGN_2026-09-30.md`` 결정 14 · 화면 세션 합의
(``scratch/capability_first/screen_contract_agreed_with_f7.md`` — 화면은 이미 이 칸을 보내고, 2.4 봉투는 모르는 칸을 거절한다).
반례 양쪽 — 받아야 할 것 · 막아야 할 것. 검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator  # noqa: E402

SCHEMA = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas" / "airo_request.json"
BASE = {"asker": {"login_id": "demo.policy.001"}, "query": "설정온도를 1도, 2도 올리면 에너지가 얼마나 줄어?"}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _ok(inst) -> bool:
    return not list(Draft202012Validator(_schema()).iter_errors(inst))


def test_interpretation_is_declared_once_and_optional():
    schema = _schema()
    assert schema["properties"]["interpretation"] == {"$ref": "#/$defs/Interpretation"}
    assert "interpretation" not in schema["required"]
    part = schema["$defs"]["Interpretation"]
    assert part["additionalProperties"] is False and part["required"] == ["frame_id"]
    # from_request_id 의 길이 한도 = 봉투 request_id 와 같다(같은 값이 두 칸을 오간다)
    assert part["properties"]["from_request_id"]["maxLength"] == schema["properties"]["request_id"]["maxLength"]
    Draft202012Validator.check_schema(schema)


def test_envelopes_valid_before_2_5_stay_valid():
    accept = [BASE,
              {**BASE, "target": {"kind": "region", "ids": ["region:11680"]}},
              {**BASE, "continuation": {"prior_request_id": "STUDIO-ASK-1"}},
              {**BASE, "intent": "both", "surface": "studio", "tool_input_mode": "literal-v1"}]
    assert len(accept) == 4 and all(_ok(e) for e in accept)


def test_interpretation_accepts_the_shape_the_screens_send():
    accept = [{**BASE, "interpretation": {"frame_id": "Q-SET"}},
              {**BASE, "interpretation": {"frame_id": "Q-MEA", "from_request_id": "AIROS-UI-0123456789abcdef"}},
              {**BASE, "interpretation": {"frame_id": "a" * 64}},
              {**BASE, "interpretation": {"frame_id": "Q-SET:ladder.v1_x", "from_request_id": "r" * 120}}]
    assert len(accept) == 4
    for envelope in accept:
        assert _ok(envelope), envelope


def test_interpretation_blocks_other_shapes():
    reject = [{**BASE, "interpretation": {}},                                            # frame_id 없음
              {**BASE, "interpretation": {"from_request_id": "R-1"}},                      # frame_id 없음
              {**BASE, "interpretation": {"frame_id": ""}},                               # 0자
              {**BASE, "interpretation": {"frame_id": "a" * 65}},                         # 65자
              {**BASE, "interpretation": {"frame_id": "Q SET"}},                          # 공백
              {**BASE, "interpretation": {"frame_id": "설정온도"}},                        # 허용 글자 밖
              {**BASE, "interpretation": {"frame_id": "Q-SET/../x"}},                     # 경로 글자
              {**BASE, "interpretation": {"frame_id": "Q-SET", "from_request_id": ""}},   # 빈 요청 번호
              {**BASE, "interpretation": {"frame_id": "Q-SET", "from_request_id": "r" * 121}},
              {**BASE, "interpretation": {"frame_id": "Q-SET", "slots": {"x": 1}}},       # 모르는 칸
              {**BASE, "interpretation": "Q-SET"},                                        # 객체가 아님
              {**BASE, "interpretation": None},
              {**BASE, "interpretations": {"frame_id": "Q-SET"}}]                         # 최상위의 모르는 칸은 여전히 거절
    assert len(reject) == 13
    for envelope in reject:
        assert not _ok(envelope), envelope
