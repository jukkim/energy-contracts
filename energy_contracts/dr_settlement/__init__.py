"""DR 정산 canonical 커널 — gridbridge live + be-3d a21 공유 SSOT (Layer 1).

보상 − 미이행 패널티 = 순정산. gridbridge settle_event 와 be-3d a21 중복 통합.
SSOT 위치: 공모전/2026-04-24_AI챔피언_*/docs/AGENT_EXPANSION_PLAN.md §3.5.
"""
from __future__ import annotations

from .policy import (
    DR_CAPACITY_KRW_PER_KW_YEAR,
    DR_PENALTY_KRW_PER_KWH,
    DREventSettlement,
    SETTLEMENT_FACTOR,
    SMP_FALLBACK_KRW,
    settle_dr_event,
)

__all__ = [
    "DREventSettlement",
    "settle_dr_event",
    "SETTLEMENT_FACTOR",
    "SMP_FALLBACK_KRW",
    "DR_PENALTY_KRW_PER_KWH",
    "DR_CAPACITY_KRW_PER_KW_YEAR",
]
