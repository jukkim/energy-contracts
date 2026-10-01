# -*- coding: utf-8 -*-
"""0.3.76(2026-10-01) — 새 스키마 ``airo_product_route.json``(airo-product-route/v1 · 통합 화면 상품 고르기).

근거 = 공모전 ``docs/INTEGRATED_INTERFACE_AND_LLM_ROLE_RESEARCH_2026-10-01.md`` D1(사용자 결정 10-01 09:5x — 통합 화면 + LLM 이 상품을 고른다)과
화면 세션과 합의한 계약(``POST /v2/route-product``). 요청·응답 두 정의를 반례 양쪽(받아야 할 것 · 막아야 할 것)으로 본다. 질의자 모양은 정본
``airo_request.json#/$defs/Asker`` 를 가리키므로 EC 스키마 전부를 한 레지스트리에 올려 읽는다(`test_interface_contracts` 와 같은 방법).
검사한 건수를 단언한다(0 건이면 실패). 질의 봉투의 표면 목록에 stage 를 넣지 않았다는 것도 본다(상품 고르기는 자기 계약).
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
PRODUCTS = ["studio", "airos", "be3d", "agentleague", "mcp"]


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


_REG = _registry()


def _validator(part: str | None = None) -> Draft202012Validator:
    ref = f"{BASE}{NAME}" + (f"#/$defs/{part}" if part else "")
    return Draft202012Validator({"$ref": ref}, registry=_REG)


def _ok(part: str | None, inst) -> bool:
    return not list(_validator(part).iter_errors(inst))


REQ = {"question_ko": "우리 점포 전기 줄이는 방법", "surface": "stage"}
RESP = {"schema": "airo-product-route/v1", "product": "airos", "why_ko": "질문이 '우리 점포' 운영을 묻습니다.",
        "alternatives": [{"product": "studio", "why_ko": "값·표로도 답할 수 있습니다."}], "source": "llm",
        "model": "us.anthropic.claude-sonnet-4-6"}


def test_schema_is_valid_and_carries_headers():
    schema = _load(NAME)
    Draft202012Validator.check_schema(schema)
    assert schema["$id"] == BASE + NAME
    assert schema["_usage"] == "runtime-validate"
    assert "ems_transformer" in schema["_consumers"] and "energy-decision-studio" in schema["_consumers"]
    assert schema["version"] == "1.0"
    assert schema["$defs"]["Product"]["enum"] == PRODUCTS            # 이름·순서(결정 문서 D1 의 순서)
    assert schema["$defs"]["Response"]["properties"]["schema"]["const"] == "airo-product-route/v1"
    assert schema["$defs"]["Response"]["properties"]["alternatives"]["maxItems"] == 2
    assert schema["$defs"]["WhyKo"]["maxLength"] == 120


def test_asker_points_at_the_canonical_envelope_definition():
    """질의자 모양 사본을 두지 않는다 — airo_request 의 Asker 를 가리키고, 그 정의로 같이 판정한다."""
    schema = _load(NAME)
    assert schema["$defs"]["Request"]["properties"]["asker"]["$ref"] == "airo_request.json#/$defs/Asker"
    asker_ok = {"login_id": "demo.policy.001", "alias": "정책 담당 공무원", "persona": "P-GOV"}
    asker_bad = {"login_id": "Demo Policy", "persona": "P-GOV"}
    envelope_asker = Draft202012Validator({"$ref": f"{BASE}airo_request.json#/$defs/Asker"}, registry=_REG)
    assert not list(envelope_asker.iter_errors(asker_ok)) and _ok("Request", {**REQ, "asker": asker_ok})
    assert list(envelope_asker.iter_errors(asker_bad)) and not _ok("Request", {**REQ, "asker": asker_bad})


def test_requests_accepted():
    accept = [
        REQ,
        {**REQ, "asker": {"login_id": "demo.policy.001", "persona": "P-GOV"}},
        {**REQ, "prior_product": "be3d"},
        {**REQ, "prior_product": "studio", "continuation": {"prior_request_id": "studio-abc-1"}},
        {**REQ, "continuation": {"prior_request_id": "x", "prior_question_ko": "설정온도를 1도 올리면?"}},
        {"question_ko": "Claude 에서 우리 건물 데이터 쓰려면", "surface": "stage", "prior_product": "mcp"},
    ]
    checked = 0
    for inst in accept:
        assert _ok("Request", inst), inst
        assert _ok(None, inst), inst                       # 문서 뿌리(oneOf 요청|응답)도 요청으로 받는다
        checked += 1
    assert checked == len(accept) == 6


def test_requests_blocked():
    block = [
        {},                                                                   # 질문 없음
        {"surface": "stage"},
        {"question_ko": "", "surface": "stage"},                              # 빈 글
        {"question_ko": "   ", "surface": "stage"},                           # 공백만
        {"question_ko": "x" * 4001, "surface": "stage"},                      # 길이 상한
        {"question_ko": "질문"},                                               # surface 없음
        {**REQ, "surface": "studio"},                                         # 다른 표면은 자기 봉투를 쓴다
        {**REQ, "surface": "Stage"},
        {**REQ, "prior_product": "lab"},                                      # 목록 밖 상품(Lab = BE-3D 저작 환경)
        {**REQ, "prior_product": "canvas"},
        {**REQ, "prior_product": "AIROS"},
        {**REQ, "product": "airos"},                                          # 모르는 칸(요청이 상품을 정하지 않는다)
        {**REQ, "target": {"kind": "region", "ids": ["region:11680"]}},       # 대상은 이 계약의 칸이 아니다
        {**REQ, "asker": {"login_id": "demo.policy.001", "role": "admin"}},  # 질의자 정본 모양 밖 칸
        {**REQ, "continuation": {}},                                          # 앞 요청 번호 없음
        {**REQ, "continuation": {"prior_request_id": ""}},
        {**REQ, "continuation": {"prior_request_id": "a", "requested_tool": "x"}},
        {**REQ, "continuation": True},
    ]
    checked = 0
    for inst in block:
        assert not _ok("Request", inst), inst
        checked += 1
    assert checked == len(block) == 18


def test_responses_accepted():
    accept = [
        RESP,
        {**RESP, "alternatives": []},
        {**RESP, "alternatives": [{"product": "studio", "why_ko": "값·표로 답합니다."},
                                  {"product": "be3d", "why_ko": "지도로도 보입니다."}]},
        {k: v for k, v in RESP.items() if k != "model"} | {"source": "rule"},
        {k: v for k, v in RESP.items() if k != "model"} | {"source": "fallback", "product": "studio", "alternatives": []},
        {**RESP, "why_ko": "가" * 120},
    ]
    checked = 0
    for inst in accept:
        assert _ok("Response", inst), inst
        assert _ok(None, inst), inst
        checked += 1
    assert checked == len(accept) == 6


def test_responses_blocked():
    no_model = {k: v for k, v in RESP.items() if k != "model"}
    block = [
        {**RESP, "schema": "airo-product-route/v2"},
        {**RESP, "product": "lab"},                                           # 목록 밖 상품
        {**RESP, "product": None},
        {**RESP, "why_ko": ""},
        {**RESP, "why_ko": "가" * 121},                                       # 한 줄 길이 상한
        {**RESP, "why_ko": "첫 줄\n둘째 줄"},                                  # 줄바꿈 금지
        {**RESP, "why_ko": "끝 줄바꿈\n"},                                     # 끝 줄바꿈도(정규식 $ 함정)
        {**RESP, "alternatives": [{"product": "studio", "why_ko": "가나"}] * 3},  # 대안 셋
        {**RESP, "alternatives": [{"product": "mars", "why_ko": "가나"}]},
        {**RESP, "alternatives": [{"product": "studio"}]},                    # 대안 이유 없음
        {**RESP, "alternatives": [{"product": "studio", "why_ko": "가나", "score": 0.4}]},
        {**RESP, "source": "guess"},
        {**RESP, "asker": {"login_id": "demo.policy.001"}},                   # 응답은 질의자를 정하지 않는다
        {**RESP, "target": {"kind": "region"}},                               # 대상도
        {**RESP, "confidence": 0.9},                                          # 모르는 칸
        no_model,                                                             # llm 인데 모델 이름 없음
        {**RESP, "source": "rule"},                                           # rule 인데 모델 이름 있음
        {k: v for k, v in RESP.items() if k != "alternatives"},              # 대안 칸 자체는 필수(빈 목록 허용)
    ]
    checked = 0
    for inst in block:
        assert not _ok("Response", inst), inst
        checked += 1
    assert checked == len(block) == 18


def test_root_does_not_accept_a_mix_of_request_and_response():
    assert not _ok(None, {**REQ, **RESP})
    assert not _ok(None, {"question_ko": "질문", "surface": "stage", "source": "llm"})


def test_query_envelope_surface_list_is_unchanged():
    """상품 고르기는 질의가 아니다 — 질의 봉투의 표면 목록에 stage 를 넣지 않는다(2.6 목록 그대로)."""
    enum = _load("airo_request.json")["properties"]["surface"]["enum"]
    assert "stage" not in enum
    assert enum == ["mcp", "studio", "lab", "airos", "agentleague", "canvas"]


def test_index_lists_the_new_schema():
    text = (SCHEMAS / "_index.yaml").read_text(encoding="utf-8")
    assert "{$ref: 'airo_product_route.json'}" in text


def test_generated_model_carries_both_definitions():
    from energy_contracts._pydantic_models import airo_product_route as m
    req = m.Request.model_validate(REQ)
    assert req.surface == "stage"
    resp = m.Response.model_validate(RESP)
    assert resp.product.value == "airos" and resp.source.value == "llm"
    assert [p.value for p in m.Product] == PRODUCTS
    with pytest.raises(Exception):
        m.Request.model_validate({**REQ, "product": "airos"})
    with pytest.raises(Exception):
        m.Response.model_validate({**RESP, "product": "lab"})
