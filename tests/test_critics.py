"""C1 검증 — 4 종 Critic mock 시나리오 통과율 ≥ 90%.

§11 L1 진입 게이트 산출 검증.

이전 위치: be-3d `tests/test_critics.py` (2026-05-24, commit `tests/test_critics.py`).
2026-05-27: SSOT_GOVERNANCE §9 도메인 횡단 분리 원칙에 따라 EC 로 이동.
"""

from __future__ import annotations

import pytest

from energy_contracts.critics import (
    CarbonCritic,
    Critic,
    DataCritic,
    LegalCritic,
    SafetyCritic,
    Verdict,
)


CLEAN_ANSWERS = [
    "전력 0.4173 kgCO2/kWh 적용. 냉방 setpoint 26°C, PMV 0.3 유지.",
    "지역난방 0.178 kgCO2/kWh, ESS SOC 30% 유지하며 PV 30kW 활용.",
    "ZEB 5등급 의무화 대상 (2025.6 시행). 가스 0.202 kgCO2/kWh.",
    "비공개 한국 실측 데이터셋 검증 결과 NRMSE 12.3%. 조명 50% 절감.",
    "건축법 제65조(에너지 절약 계획서) 제출 대상. 난방 22°C.",
    "K-ETS 4기 (2026.1.1 시행) 대상 — 발전 유상할당 50%.",
    "Site A, Site B 데이터로 학습. PMV -0.3, 냉방 25°C.",
    "Held-out Korean validation set 으로 calibration 검증.",
    "녹색건축법에 따른 ZEB 인증 추진. ESS SOC 25%, 조명 60%.",
    "현행 PE factor 지역난방 0.728 (2025.1.1 정정) 적용.",
]


VIOLATION_ANSWERS = {
    "c_legal": [
        "BEEC 기준에 따라 검증.",
        "건축법 제65조에 따라 90.7%의 건물이 절약 대상.",
        "녹색건축법 제17조에 따르면 인증 필요.",
        "그린리모델링 민간 이자지원 활용 가능.",
        "건축법 제65조 적용.",
    ],
    "c_carbon": [
        "전력 0.4747 kgCO2/kWh 적용 (구버전).",
        "전력 0.55 kgCO2/kWh 로 산정.",
        "가스 0.35 kgCO2/kWh 사용.",
        "지역난방 0.40 kgCO2/kWh 적용.",
        "electricity 0.60 kgCO2eq.",
    ],
    "c_safety": [
        "냉방 15°C 권장.",
        "난방 32°C 까지 가동.",
        "PMV 1.2 허용.",
        "ESS SOC 5% 까지 방전.",
        "조명 10% 디밍.",
    ],
    "c_data": [
        "한수원 데이터로 학습 완료.",
        "IITP 가상 EMS 35,136행 사용.",
        "레플러스 검침으로 calibration.",
        "GS25 224점포 데이터 적용.",
        "에너지엑스 BACnet 실측.",
    ],
}


@pytest.fixture
def critics() -> dict[str, Critic]:
    return {
        "c_legal": LegalCritic(),
        "c_carbon": CarbonCritic(),
        "c_safety": SafetyCritic(),
        "c_data": DataCritic(),
    }


def test_clean_answers_pass_all_critics(critics):
    """깨끗한 답 → 4 종 모두 PASS 또는 WARN."""
    for ans in CLEAN_ANSWERS:
        for name, c in critics.items():
            r = c.review(ans)
            assert r.verdict != Verdict.FAIL, (
                f"{name} 가 깨끗한 답에서 FAIL: {ans!r} / 위반: {r.violations}"
            )


def test_violation_answers_caught(critics):
    """위반 답 → 해당 Critic FAIL 또는 WARN."""
    for critic_key, bad_answers in VIOLATION_ANSWERS.items():
        c = critics[critic_key]
        caught = 0
        for ans in bad_answers:
            r = c.review(ans)
            if r.verdict in (Verdict.WARN, Verdict.FAIL):
                caught += 1
        rate = caught / len(bad_answers)
        assert rate >= 0.8, (
            f"{critic_key} 위반 검출률 {rate:.0%} < 80%. "
            f"통과한 답: {[a for a in bad_answers if c.review(a).verdict == Verdict.PASS]}"
        )


def test_pass_rate_gate_per_critic(critics):
    """§11 L1 진입 게이트: 깨끗한 답에서 통과율 ≥ 90%."""
    for name, c in critics.items():
        passed = sum(1 for a in CLEAN_ANSWERS if c.review(a).verdict == Verdict.PASS)
        rate = passed / len(CLEAN_ANSWERS)
        assert rate >= 0.9, (
            f"{name} 통과율 {rate:.0%} < 90% (§11 L1 게이트 미달)"
        )


def test_data_critic_zero_tolerance(critics):
    """C-Data 는 NDA 노출 1 건만으로 FAIL."""
    c = critics["c_data"]
    r = c.review("한수원 데이터로 학습")
    assert r.verdict == Verdict.FAIL
    assert any(v["rule"] == "nda_source_exposed" for v in r.violations)


def test_carbon_critic_zero_tolerance(critics):
    """C-Carbon 도 SSOT 불일치 1 건만으로 FAIL (2026-05-27 audit 강화)."""
    c = critics["c_carbon"]
    r = c.review("전력 0.55 kgCO2/kWh 적용.")
    assert r.verdict == Verdict.FAIL, (
        f"Carbon SSOT 불일치 1 건이 FAIL 이어야 함. 실제: {r.verdict} / {r.violations}"
    )
    assert any(v["rule"] == "factor_mismatch" for v in r.violations)

    r_outdated = c.review("전력 0.4747 kgCO2/kWh 적용 (구버전).")
    assert r_outdated.verdict == Verdict.FAIL
    assert any(v["rule"] == "outdated_electricity_factor" for v in r_outdated.violations)


def test_critic_result_serializable(critics):
    """CriticResult.to_dict() 직렬화 — Layer 2 audit chain 적재 호환."""
    c = critics["c_legal"]
    r = c.review("BEEC 기준 적용")
    d = r.to_dict()
    assert d["critic"] == "c_legal"
    assert d["verdict"] in {"pass", "warn", "fail"}
    assert isinstance(d["violations"], list)
