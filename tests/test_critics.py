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
    "지역난방 0.126 kgCO2/kWh, ESS SOC 30% 유지하며 PV 30kW 활용.",
    "ZEB 5등급 의무화 대상 (2025.6 시행). 가스 0.2036 kgCO2/kWh.",
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
        "냉방 setpoint 226°C 까지 과부하.",  # 사냥꾼 FIX: 3자리 setpoint (구 \d{1,2} 가 "26"으로 절단→fail-open)
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


def test_carbon_overclaim_fires_with_independent_known(critics):
    """C-Carbon overclaim: 주장(claimed) > 독립 근거(known)×1.25 → FAIL (P2-c, 2026-06-17).

    W4 실 Critic 스왑 시 게이트가 살아있어야 한다 — claimed/known 은 context 의 별개 키.
    """
    c = critics["c_carbon"]
    # claimed 40% vs known 20% → 0.4 > 0.2×1.25=0.25 → overclaim
    r = c.review("절감 가능", {"claimed_reduction_pct": 0.4, "known_rate": 0.2})
    assert r.verdict == Verdict.FAIL, f"overclaim 단건 → FAIL. 실제 {r.verdict} / {r.violations}"
    ov = [v for v in r.violations if v["rule"] == "overclaim"]
    assert ov and ov[0]["known_rate"] == 0.2 and ov[0]["claimed_reduction_pct"] == 0.4


def test_carbon_overclaim_silent_when_within_threshold(critics):
    """claimed ≤ known×1.25 → overclaim 미발화 (정직 주장은 통과)."""
    c = critics["c_carbon"]
    r = c.review("절감", {"claimed_reduction_pct": 0.24, "known_rate": 0.2})  # 0.24 ≤ 0.25
    assert not any(v["rule"] == "overclaim" for v in r.violations)
    assert r.verdict == Verdict.PASS


def test_carbon_overclaim_dead_gate_guard_no_fabricated_known(critics):
    """self-reference 방지: known 부재 시 claimed 로 대체하지 않고 overclaim **skip**.

    known 을 claimed 에서 파생하면 게이트가 죽는다 — known 없으면 검사 자체를 건너뛴다.
    claimed 0.3(비현실 상한 0.5 미만)·known 부재 → 위반 0, PASS 여야 한다.
    """
    c = critics["c_carbon"]
    r = c.review("절감", {"claimed_reduction_pct": 0.3})  # known_rate 없음
    assert not any(v["rule"] == "overclaim" for v in r.violations), (
        "known 부재인데 overclaim 발화 = claimed 를 known 으로 둔갑(죽은 게이트)"
    )
    assert r.verdict == Verdict.PASS
    # known=0(분모 0) 도 동일하게 skip
    r0 = c.review("절감", {"claimed_reduction_pct": 0.9, "known_rate": 0})
    assert not any(v["rule"] == "overclaim" for v in r0.violations)


def test_carbon_implausible_reduction_independent_of_known(critics):
    """claimed > 50% → 비현실 위반 (독립 근거 유무 무관)."""
    c = critics["c_carbon"]
    r = c.review("절감", {"claimed_reduction_pct": 0.7})
    assert any(v["rule"] == "implausible_reduction" for v in r.violations)
    assert r.verdict == Verdict.FAIL


def test_carbon_overclaim_backward_compatible_no_context(critics):
    """context 없는 기존 호출(DR gate 등)은 overclaim 무관 — 회귀 0."""
    c = critics["c_carbon"]
    r = c.review("전력 0.4173 kgCO2/kWh 적용.")  # 정상 factor, context 없음
    assert r.verdict == Verdict.PASS
    assert not any(v["rule"] in ("overclaim", "implausible_reduction") for v in r.violations)


def test_safety_critic_hard_interlock_zero_tolerance(critics):
    """C-Safety hard interlock (setpoint/SOC) 은 단건만으로 FAIL — 룰별 차등 정책.

    사냥꾼 라운드 M1/M12 (사용자 결정 2026-06-08): 물리 interlock 은 Carbon/Data 와
    동일하게 zero-tolerance. 단건 setpoint 범위초과 / ESS SOC floor 미만 → FAIL.
    """
    c = critics["c_safety"]
    r_setpoint = c.review("냉방 setpoint 226°C 까지 과부하.")
    assert r_setpoint.verdict == Verdict.FAIL, (
        f"단건 setpoint 초과는 hard interlock → FAIL. 실제: {r_setpoint.verdict}"
    )
    assert any(v["rule"] == "hvac_setpoint_out_of_range" for v in r_setpoint.violations)

    r_soc = c.review("ESS SOC 5% 까지 방전.")
    assert r_soc.verdict == Verdict.FAIL
    assert any(v["rule"] == "ess_soc_below_floor" for v in r_soc.violations)


def test_safety_critic_soft_rule_single_warns(critics):
    """C-Safety soft 룰 (조명/PMV) 단건은 WARN (FAIL 아님) — 룰별 차등 정책."""
    c = critics["c_safety"]
    r_light = c.review("조명 10% 디밍.")
    assert r_light.verdict == Verdict.WARN, (
        f"단건 조명 floor 미만은 soft → WARN. 실제: {r_light.verdict}"
    )
    assert any(v["rule"] == "lighting_below_floor" for v in r_light.violations)

    r_pmv = c.review("PMV 1.2 허용.")
    assert r_pmv.verdict == Verdict.WARN
    assert any(v["rule"] == "pmv_out_of_comfort" for v in r_pmv.violations)


def test_data_critic_public_mode_real_data(critics):
    """C-Data public 노출 모드 — 익명화 없이 '실측'/'measured' 언급 시 FAIL.

    사냥꾼 라운드 LOW (2026-06-08): public-mode 분기가 테스트 미보호였고 영문
    'measured'/'real building' 미커버였음. 한/영 모두 검출 + 익명화 시 통과 확인.
    """
    c = critics["c_data"]
    pub = {"disclose_mode": "public"}
    # 한글 '실측' 익명화 없이 → FAIL
    r_ko = c.review("실측 데이터로 검증함.", pub)
    assert r_ko.verdict == Verdict.FAIL
    assert any(v["rule"] == "real_data_mentioned_without_anonymization" for v in r_ko.violations)
    # 영문 'measured' 익명화 없이 → FAIL (이전엔 미커버)
    r_en = c.review("Validated on measured building data.", pub)
    assert r_en.verdict == Verdict.FAIL
    # 익명화 표현 있으면 통과
    r_ok = c.review("비공개 한국 실측 데이터셋으로 검증.", pub)
    assert r_ok.verdict == Verdict.PASS


def test_critic_result_serializable(critics):
    """CriticResult.to_dict() 직렬화 — Layer 2 audit chain 적재 호환."""
    c = critics["c_legal"]
    r = c.review("BEEC 기준 적용")
    d = r.to_dict()
    assert d["critic"] == "c_legal"
    assert d["verdict"] in {"pass", "warn", "fail"}
    assert isinstance(d["violations"], list)
