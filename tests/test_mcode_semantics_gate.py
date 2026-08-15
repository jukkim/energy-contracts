"""M-code 의미 게이트가 **진짜로 잡는가** — 가드의 가드.

2026-06-22 에 M-code 통일을 했는데 2026-08-15 에 또 어긋났다. 근인은
**회귀 가드를 소비자 저장소 한 곳(agentleague)에만 넣은 것**이다.
이번엔 정본 저장소에 두되, **그 게이트가 공허하지 않은지**도 시험한다.

첫 판본은 실제로 공허했다 — 알려진 4 건 오매핑을 **0 건으로 통과**시켰다
(JSON `"M12": "값"` 형태를 정규식이 못 읽었고, `냉방설정온도조정` 처럼
남의 낱말이 없는 오매핑은 원리적으로 못 잡았다).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import verify_mcode_semantics as G  # noqa: E402


def test_정본을_읽는다():
    st = G.canon()
    assert len(st) == 23, f"정본이 23 종이 아니다: {len(st)}"
    assert st["M07"]["name_en"] == "DCV"
    assert st["M17"]["name_en"] == "LightingControl"
    assert st["M03"]["name_en"] == "Staging"


@pytest.mark.parametrize("code,label", [
    ("M07", "냉방설정온도조정"),   # 실제 M07 = CO2 수요제어환기
    ("M03", "야간냉방차단"),       # 실제 M03 = 냉동기·보일러 대수 제어
    ("M12", "ESS방전"),           # 실제 M12 = 통합+PMV0.5
    ("M09", "야간조명차단"),       # 실제 M09 = 피크 전 프리쿨링
])
def test_알려진_오매핑을_잡는다(code, label):
    """2026-08-15 에 Lab 에서 실제로 발견된 넷. 이걸 놓치면 게이트가 무의미하다."""
    assert G.check_declared(code, label, G.canon()) is not None, (
        f"{code}({label}) 를 통과시켰다 — 이게 바로 재발한 오매핑이다")


@pytest.mark.parametrize("code,label", [
    ("M07", "CO2 수요제어환기"),
    ("M07", "DCV"),
    ("M03", "냉동기·보일러 대수 제어"),
    ("M12", "통합+PMV0.5"),
    ("M17", "조명 제어(디밍)"),
    ("M09", "피크 전 프리쿨링"),
])
def test_정본대로면_통과한다(code, label):
    """과잉 차단 방지 — 맞게 쓴 것을 막으면 사람이 게이트를 끈다."""
    assert G.check_declared(code, label, G.canon()) is None, (
        f"{code}({label}) 는 정본과 맞는데 막았다")


def test_나열은_이름이_아니다():
    assert G.check_foreign("M01", "ScheduleOpt · M06=NightCycle · M07=DCV") is None


def test_이력_인용_패턴이_있다():
    """과거 표기를 인용한 줄을 고치면 이력이 거짓이 된다."""
    assert G.HISTORICAL.search("과거 M07(조명)은 구 체계 표기였다")
    assert not G.HISTORICAL.search('STRATEGIES = {"M07": "조명"}')


def test_등록_저장소가_비어있지_않다():
    """0 개를 훑고 통과하는 가드를 이 저장소에서 이미 겪었다."""
    assert len(G.REPOS) >= 10
