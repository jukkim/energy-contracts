# -*- coding: utf-8 -*-
"""0.3.77(2026-10-01) — data_classification 1.5: 화면 배지 낱말(``display_badges_ko`` · 낱말마다 ``badge_ko``) · 방법 한 줄(``short_ko``) ·
별칭 ``synthetic_demo_fixture → virtual``.

근거 = 캠페인 ``docs/UIUX_CONSISTENCY_RESEARCH_2026-10-01.md`` 결정 U1(배지 '측정 → 실측' · '참고치 → 참고')·U4(분류 없음 = '표시 없음') ·
§2 '배지 낱말·짧은 방법 줄 = EC data_classification(badge_ko·short_ko 추가)' · 표 H1(AgentLeague 합성 시연 자료가 '못 잼 · 분류 미표시'로 보였다).
반례 양쪽 — 받아야 할 것 · 막아야 할 것. 검사한 건수를 단언한다(0 건이면 실패).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "energy_contracts" / "schemas" / "data_classification.json"
#: 사용자 결정(U1·U4)의 배지 낱말 7개 — 이 시험이 정본을 대신하지 않는다(정본 = 스키마). 값이 바뀌면 결정이 바뀐 것이다
BADGES_7 = {"실측", "추정", "예측", "참고", "가상", "혼합", "표시 없음"}

_spec = importlib.util.spec_from_file_location("_t0372", Path(__file__).with_name("test_declared_assumptions_0372.py"))
_t0372 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t0372)
strict_additive, _at_tag = _t0372.strict_additive, _t0372._at_tag

ALLOWED_CHANGES = {"/version", "/updated", "/$comment"}


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _vocab() -> dict:
    return _schema()["default"]["classification"]


def test_display_badges_cover_every_display_class_with_the_seven_words():
    schema = _schema()
    classes = schema["$defs"]["EvidenceDisplayClass"]["enum"]
    badges = _vocab()["display_badges_ko"]
    assert list(badges) == classes                           # 표시 등급마다 하나 · 순서도 같다(빠진 등급 없음)
    assert set(badges.values()) == BADGES_7, set(badges.values())
    assert badges["synthetic"] == badges["virtual"] == "가상"
    assert badges["unknown"] == "표시 없음" and badges["reference"] == "참고" and badges["measured"] == "실측"
    assert len(classes) == 8


def test_every_word_badge_is_its_display_class_badge_and_has_a_short_line():
    vocab = _vocab()
    badges = vocab["display_badges_ko"]
    checked = 0
    for word, row in vocab["words"].items():
        assert row["badge_ko"] == badges[row["display_class"]], word
        short = row["short_ko"]
        assert isinstance(short, str) and short.strip() == short and 2 <= len(short) <= 30, (word, short)
        assert "\n" not in short and not short.endswith(("다", "다.")), (word, short)    # 명사형(표 아래 한 줄)
        checked += 1
    assert checked == len(_schema()["$defs"]["ClassificationWord"]["enum"]) == 17


def test_counterexamples_badges_are_not_confused():
    """막아야 할 것: 추정·시뮬레이션 값에 '실측' 배지 · 분류 모름에 '가상' · 혼합에 한 쪽 배지."""
    words = _vocab()["words"]
    for word in ("simulated", "calibrated", "imputed", "estimated"):
        assert words[word]["badge_ko"] == "추정", word
    assert words["measured"]["badge_ko"] == "실측"
    assert words["measured_with_imputed"]["badge_ko"] == "혼합"     # 실측 + 채움 = 실측이 아니다
    assert words["unknown"]["badge_ko"] == "표시 없음"
    assert words["mixed"]["badge_ko"] == "혼합"
    for word in ("virtual", "synthetic", "mock"):
        assert words[word]["badge_ko"] == "가상", word
    for word in ("certified", "external", "reference", "declared", "assumed"):
        assert words[word]["badge_ko"] == "참고", word


def test_synthetic_demo_fixture_alias_reads_as_virtual_and_others_stay_unknown():
    from energy_contracts import rules_pure as rp
    table = _vocab()
    accept = ["synthetic_demo_fixture", "SYNTHETIC_DEMO_FIXTURE", " synthetic_demo_fixture "]
    for word in accept:
        assert rp.ec_classification_normalize(word, table) == "virtual", word
        meta = rp.ec_classification_meta(word, table)
        assert meta["badge_ko"] == "가상" and meta["virtual"] is True, meta
    reject = ["synthetic_demo", "demo_fixture", "synthetic-demo-fixture", "fixture", ""]
    for word in reject:
        assert rp.ec_classification_normalize(word, table) == "unknown", word
        assert rp.ec_classification_meta(word, table)["badge_ko"] == "표시 없음", word
    assert len(accept) + len(reject) == 8


def test_additive_against_the_0376_tag():
    old = _at_tag("v0.3.76", "data_classification.json")
    if old is None:
        pytest.skip("[해당 없음] git 태그 v0.3.76 을 못 읽었다 — 통과가 아니다(못 잼)")
    problems, checked = strict_additive(old, _schema(), "", ALLOWED_CHANGES, "data_classification.json")
    assert not problems, problems
    assert checked >= 150, checked                        # 문서 잎 전부(0 건이면 그것이 사고다)


def test_generated_constants_carry_the_badges():
    gen = ROOT.parents[1] / "8.simulation" / "_shared" / "_generated_constants.py"
    if not gen.is_file():
        pytest.skip("[해당 없음] 8.simulation/_shared 생성본이 없다 — 통과가 아니다(못 잼)")
    spec = importlib.util.spec_from_file_location("_gen_0377", gen)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    vocab = mod.DATA_CLASSIFICATION_VOCAB
    assert vocab["display_badges_ko"] == _vocab()["display_badges_ko"]
    assert vocab["words"]["simulated"]["short_ko"] == _vocab()["words"]["simulated"]["short_ko"]
    assert vocab["aliases"]["synthetic_demo_fixture"] == "virtual"
