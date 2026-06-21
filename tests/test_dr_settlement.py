"""DR 정산 canonical 커널 — gridbridge + be-3d a21 공유 SSOT 단위테스트.

보상(한전 공식) · 미이행 패널티 · 순정산 · target 부재 backward-compat.
SSOT: 공모전/2026-04-24_AI챔피언_*/docs/AGENT_EXPANSION_PLAN.md §3.5.
"""
from __future__ import annotations

import pytest

from energy_contracts.dr_settlement import SETTLEMENT_FACTOR, settle_dr_event


def test_gross_matches_hanjeon_formula():
    s = settle_dr_event(100.0, 100.0, 2.0, smp_krw=120.0)
    assert s.gross_krw == pytest.approx(100 * 2 * 120 * SETTLEMENT_FACTOR)
    assert s.penalty_krw == 0
    assert s.net_krw == s.gross_krw
    assert s.compliant is True


def test_shortfall_incurs_penalty():
    # target 100, 감축 70, 2h → 부족 30kW×2h=60kWh × 120 = 7,200
    s = settle_dr_event(70.0, 100.0, 2.0, smp_krw=120.0)
    assert s.penalty_krw == pytest.approx(60 * 120)
    assert s.net_krw == s.gross_krw - s.penalty_krw
    assert s.compliant is False
    assert s.performance_ratio == pytest.approx(0.7)


def test_no_target_is_compensation_only():
    # target=0 → 패널티 0 (gridbridge backward-compat: 기존 보상만 동작 보존)
    s = settle_dr_event(100.0, 0.0, 2.0, smp_krw=120.0)
    assert s.penalty_krw == 0
    assert s.net_krw == s.gross_krw


def test_overdelivery_no_overpay_no_penalty():
    s = settle_dr_event(120.0, 100.0, 1.0, smp_krw=100.0)
    assert s.gross_krw == pytest.approx(120 * 1 * 100 * SETTLEMENT_FACTOR)
    assert s.penalty_krw == 0


def test_negative_reduction_floored():
    s = settle_dr_event(-10.0, 50.0, 1.0)
    assert s.reduction_kw == 0.0
    assert s.gross_krw == 0
