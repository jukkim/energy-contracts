# -*- coding: utf-8 -*-
"""0.3.79(2026-10-01) — ``airo_product_route.json`` 1.1: 응답 ``source`` 에 ``interpretation`` 가산(한 번 해석).

근거 = 공모전 ``docs/CAPABILITY_FIRST_QUERY_DESIGN_2026-09-30.md`` §3.1(2026-10-01 19:5x 사용자 결정 — LLM 이 상품 이름을 고르지 않고 질문 해석 한 번의
결과와 질의자 권한으로 게이트웨이가 상품을 정한다). 화면 계약(product · why_ko · source · alternatives)은 그대로 — source 낱말 하나가 늘 뿐이다.
반례 양쪽: interpretation 은 model 이 있어도 없어도 받는다 · llm 은 model 필수 · rule·fallback 은 model 금지(1.0 그대로) · 모르는 source 막음.
검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")
from jsonschema import Draft202012Validator  # noqa: E402
from referencing import Registry, Resource  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
BASE = "energy-contracts/"
NAME = "airo_product_route.json"


def _registry() -> Registry:
    resources = []
    for fp in sorted(SCHEMAS.glob("*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        resources.append((data.get("$id") or BASE + fp.name,
                          Resource.from_contents(data, default_specification=referencing.jsonschema.DRAFT202012)))
    assert resources, "0 schemas loaded - that is a failure, not a pass"
    return Registry().with_resources(resources)


_REG = _registry()


def _ok(inst) -> bool:
    return not list(Draft202012Validator({"$ref": f"{BASE}{NAME}#/$defs/Response"}, registry=_REG).iter_errors(inst))


BASE_RESP = {"schema": "airo-product-route/v1", "product": "be3d", "why_ko": "질문의 ‘3D’ 말이 3D 장면 보기를 원해 BE-3D(3D 장면)로 갑니다.",
             "alternatives": []}


def test_version_and_source_words():
    schema = json.loads((SCHEMAS / NAME).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["version"] == "1.1"
    assert schema["$defs"]["Response"]["properties"]["source"]["enum"] == ["llm", "rule", "fallback", "interpretation"]


def test_interpretation_accepted_with_and_without_model():
    accept = [
        {**BASE_RESP, "source": "interpretation", "model": "us.anthropic.claude-sonnet-4-6"},
        {**BASE_RESP, "source": "interpretation"},                         # 정형 문장 지름길처럼 LLM 없이 해석
        {**BASE_RESP, "source": "llm", "model": "m"},                       # 1.0 응답 그대로
        {**BASE_RESP, "source": "rule"},
        {**BASE_RESP, "source": "fallback"},
    ]
    checked = 0
    for inst in accept:
        assert _ok(inst), inst
        checked += 1
    assert checked == len(accept) == 5


def test_model_rules_blocked_both_ways():
    block = [
        {**BASE_RESP, "source": "llm"},                                     # llm 인데 모델 없음(1.0 그대로)
        {**BASE_RESP, "source": "rule", "model": "m"},                      # rule 인데 모델 있음(1.0 그대로)
        {**BASE_RESP, "source": "fallback", "model": "m"},
        {**BASE_RESP, "source": "interpretation", "model": ""},             # 빈 모델 이름
        {**BASE_RESP, "source": "Interpretation"},
        {**BASE_RESP, "source": "classifier"},
        {**BASE_RESP, "source": "interpretation", "interpretation": {"form": "Q-SET"}},   # 해석 내용은 응답 칸이 아니다(감사에만)
    ]
    checked = 0
    for inst in block:
        assert not _ok(inst), inst
        checked += 1
    assert checked == len(block) == 7


def test_generated_model_knows_interpretation():
    from energy_contracts._pydantic_models import airo_product_route as m
    assert [s.value for s in m.Source] == ["llm", "rule", "fallback", "interpretation"]
    resp = m.Response.model_validate({**BASE_RESP, "source": "interpretation"})
    assert resp.source.value == "interpretation" and resp.model is None
