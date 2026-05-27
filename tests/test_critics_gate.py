"""CriticsGate 실시간 + batch 토론 — plan v1.8 §10.5 Track 4 검증.

- 깨끗한 dispatch → pass
- 안전 위반 (overheated setpoint) → block
- NDA fingerprint in group_id → block (Data Critic, zero-tolerance)
- mandatory 발령 → legal context 추가, regex 위반 시 warn
- cache hit: 동일 signature 재평가 skip
- batch debate: 4 종 종합 + judge_decision

이전 위치: be-3d `tests/unit/dr/test_critics_gate.py` (2026-05-27, commit `d7a5ecc`).
2026-05-27: SSOT_GOVERNANCE §9 도메인 횡단 분리 원칙에 따라 EC 로 이동.
"""
from __future__ import annotations

import pytest

from energy_contracts.critics import (
    CriticsGate,
    Verdict,
    summarize_dispatch_for_critics,
)


@pytest.fixture
def gate() -> CriticsGate:
    return CriticsGate()


def _clean_event() -> dict:
    return {
        "event_id": "kpx-sim-clean-001",
        "source": "kpx_mock",
        "group_id": "ESG-GANGNAM-OFFICE",
        "target_kw": 100.0,
        "mandatory": False,
        "window": {"start": "2026-05-27T05:00:00+00:00", "end": "2026-05-27T06:00:00+00:00"},
        "allocations": [
            {"member_id": "OFFICE-001", "reduction_kw": 20.0, "soc_pct": 30, "pmv": 0.3},
            {"member_id": "OFFICE-002", "reduction_kw": 20.0, "soc_pct": 25, "pmv": 0.2},
        ],
    }


# ─ Summary builder ────────────────────────────────────────────


def test_summary_contains_setpoint_keyword():
    """Safety Critic 의 regex 가 텍스트 안에서 'setpoint' 또는 '냉방 X°C' 를 잡을 수 있어야 한다."""
    txt = summarize_dispatch_for_critics(_clean_event())
    assert "setpoint" in txt or "냉방" in txt
    assert "°C" in txt


def test_summary_marks_mandatory():
    evt = _clean_event()
    evt["mandatory"] = True
    txt = summarize_dispatch_for_critics(evt)
    assert "mandatory" in txt or "의무" in txt


def test_summary_includes_member_ids():
    """Data Critic 의 NDA fingerprint regex 가 member_id 를 볼 수 있어야 한다."""
    evt = _clean_event()
    evt["allocations"] = [{"member_id": "한수원-사옥-A", "reduction_kw": 30.0}]
    txt = summarize_dispatch_for_critics(evt)
    assert "한수원" in txt


# ─ Realtime gate ──────────────────────────────────────────────


def test_clean_dispatch_passes(gate):
    verdict = gate.evaluate_dispatch(_clean_event())
    assert verdict.decision == "pass", (
        f"clean event should pass; got {verdict.decision} with violations="
        f"{[r.to_dict() for r in verdict.results]}"
    )
    assert verdict.cache_hit is False
    # 3 종 모두 실행됨
    names = {r.critic_name for r in verdict.results}
    assert names == {"c_safety", "c_legal", "c_data"}


def test_safety_violation_blocks_dispatch(gate):
    """과도한 kW 감축 → setpoint 시프트 추정이 28°C 초과 → Safety FAIL."""
    evt = _clean_event()
    # 1 건물에 500 kW 감축 → +10°C 시프트 추정 → 36°C (28°C 초과)
    evt["allocations"] = [{"member_id": "OFFICE-001", "reduction_kw": 500.0}]
    evt["target_kw"] = 500.0
    verdict = gate.evaluate_dispatch(evt)
    assert verdict.decision in ("block", "warn"), (
        f"unsafe setpoint should be flagged; got {verdict.decision}"
    )
    # 최소 1 개의 hvac_setpoint_out_of_range 위반
    safety_r = next(r for r in verdict.results if r.critic_name == "c_safety")
    rules = {v["rule"] for v in safety_r.violations}
    assert "hvac_setpoint_out_of_range" in rules


def test_data_nda_fingerprint_blocks(gate):
    """NDA 출처 (한수원) 가 member_id 에 노출되면 Data Critic 이 1 건만으로 block."""
    evt = _clean_event()
    evt["allocations"] = [{"member_id": "한수원-A", "reduction_kw": 20.0}]
    verdict = gate.evaluate_dispatch(evt)
    assert verdict.decision == "block"
    data_r = next(r for r in verdict.results if r.critic_name == "c_data")
    assert data_r.verdict == Verdict.FAIL
    assert any(v["rule"] == "nda_source_exposed" for v in data_r.violations)


def test_cache_hit_on_repeat_signature(gate):
    """동일 group_id/target_kw/mandatory/source/멤버 ID → cache hit."""
    evt = _clean_event()
    first = gate.evaluate_dispatch(evt)
    second = gate.evaluate_dispatch(evt)
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.decision == first.decision


def test_cache_miss_on_different_target_kw(gate):
    """target_kw 가 다르면 cache miss."""
    e1 = _clean_event()
    e2 = _clean_event()
    e2["target_kw"] = 200.0
    gate.evaluate_dispatch(e1)
    second = gate.evaluate_dispatch(e2)
    assert second.cache_hit is False


def test_clear_cache(gate):
    evt = _clean_event()
    gate.evaluate_dispatch(evt)
    gate.clear_cache()
    again = gate.evaluate_dispatch(evt)
    assert again.cache_hit is False


# ─ Batch debate (4 종) ─────────────────────────────────────────


def test_batch_debate_clean_event_passes(gate):
    verdict = gate.evaluate_batch_debate(_clean_event())
    assert verdict.judge_decision == "pass"
    assert verdict.carbon_result is not None
    assert verdict.carbon_result.critic_name == "c_carbon"


def test_batch_debate_carbon_warn(gate):
    """outcome 에 구버전 배출계수 1 건 → Carbon Critic WARN → judge=needs_review."""
    evt = _clean_event()
    outcome = {
        "emission_factor_kgco2_per_kwh": 0.4747,  # 구버전 — outdated_electricity_factor 룰 1 건
        "source_type": "전력",
        "avoided_kwh": 100.0,
    }
    verdict = gate.evaluate_batch_debate(evt, outcome=outcome)
    assert verdict.judge_decision == "needs_review"
    assert verdict.carbon_result.verdict == Verdict.WARN
    rules = {v["rule"] for v in verdict.carbon_result.violations}
    assert "outdated_electricity_factor" in rules


def test_batch_debate_includes_realtime_results(gate):
    """batch 는 realtime 3 종 결과를 포함."""
    verdict = gate.evaluate_batch_debate(_clean_event())
    names = {r.critic_name for r in verdict.realtime_results}
    assert names == {"c_safety", "c_legal", "c_data"}


def test_batch_debate_nda_in_event_fails(gate):
    """NDA in member_id → realtime block → judge=fail."""
    evt = _clean_event()
    evt["allocations"] = [{"member_id": "IITP-1", "reduction_kw": 20.0}]
    verdict = gate.evaluate_batch_debate(evt)
    assert verdict.judge_decision == "fail"
