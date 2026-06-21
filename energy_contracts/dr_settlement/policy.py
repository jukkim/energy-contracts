"""DR 정산 canonical 커널 — 도메인 횡단 SSOT (Layer 1).

gridbridge `dispatch/settlement.py`(live `dr_participation.compensation_krw` write)와
be-3d a21_dr_settlement 이 같은 정산 수식을 중복 구현하던 것을 본 패키지로 통합.
gridbridge 가 보상만(패널티 없음) 계산하던 것을 본 커널로 일원화 — 패널티 포함.

수식 (한전 DR 시장 기준):
- 보상(gross) = 감축kW × 지속h × SMP × SETTLEMENT_FACTOR(0.8).
- 패널티 = max(0, target − 감축)kWh × DR_PENALTY_KRW_PER_KWH(120). target=0 이면 0.
- 순정산(net) = gross − penalty. 과보상 없음(보상은 실 감축 기준, 패널티는 부족분만).

SSOT 위치: 공모전/2026-04-24_AI챔피언_*/docs/AGENT_EXPANSION_PLAN.md §3.5.
"""
from __future__ import annotations

from dataclasses import dataclass

SETTLEMENT_FACTOR = 0.8
SMP_FALLBACK_KRW = 120.0
DR_PENALTY_KRW_PER_KWH = 120.0      # 미이행 정산금 (인센티브 > 패널티 역전 방지)
DR_CAPACITY_KRW_PER_KW_YEAR = 5_000.0


@dataclass(frozen=True)
class DREventSettlement:
    """이벤트 1건 정산 결과 (canonical)."""

    reduction_kw: float
    target_kw: float
    duration_h: float
    smp_krw: float
    gross_krw: float            # 감축 보상 (패널티 전)
    penalty_krw: float          # 미이행 패널티
    net_krw: float              # gross − penalty (실 지급 기준)
    performance_ratio: float    # 감축 / target
    compliant: bool


def settle_dr_event(
    reduction_kw: float,
    target_kw: float,
    duration_h: float,
    *,
    smp_krw: float = SMP_FALLBACK_KRW,
    settlement_factor: float = SETTLEMENT_FACTOR,
    penalty_krw_per_kwh: float = DR_PENALTY_KRW_PER_KWH,
) -> DREventSettlement:
    """이벤트 1건 정산 — 보상 − 미이행 패널티. target=0 이면 패널티 0(보상만)."""
    reduction_kw = max(0.0, float(reduction_kw))
    target_kw = max(0.0, float(target_kw))
    duration_h = max(0.0, float(duration_h))

    gross = reduction_kw * duration_h * smp_krw * settlement_factor
    shortfall_kwh = max(0.0, target_kw - reduction_kw) * duration_h
    penalty = shortfall_kwh * penalty_krw_per_kwh
    pr = round(reduction_kw / target_kw, 3) if target_kw > 0 else 0.0
    return DREventSettlement(
        reduction_kw=round(reduction_kw, 3), target_kw=round(target_kw, 3),
        duration_h=round(duration_h, 3), smp_krw=round(smp_krw, 2),
        gross_krw=round(gross), penalty_krw=round(penalty),
        net_krw=round(gross - penalty), performance_ratio=pr,
        compliant=reduction_kw >= target_kw,
    )
