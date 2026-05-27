"""Critics — 도메인 횡단 룰 기반 검증 + 조합자 (Layer 1).

본 패키지는 어떤 도메인에서도 재사용 가능한 4 종 Critic 과 게이트 조합자를 제공한다.
도메인 컨텍스트(DR / EMS / ESG / 정책 등) 는 호출자가 텍스트로 요약해서 주입.

- `LegalCritic`  — 법령 인용 정확성 (`rules/legal-citation.md`)
- `CarbonCritic` — 배출계수 SSOT 정합 (`CARBON_EMISSION_FACTORS.yaml`)
- `SafetyCritic` — HVAC/PMV/ESS/조명 interlock
- `DataCritic`   — NDA 출처 fingerprint (`rules/private-data-disclosure.md`)
- `CriticsGate`  — 4 종 Critic 조합 + 실시간 verdict + 사후 batch debate
- `summarize_dispatch_for_critics` — DR-shape 이벤트 → 한국어 요약 (참고 헬퍼)

SSOT 위치: `myjob/docs/SSOT_GOVERNANCE.md` §9 — 도메인 횡단 로직 분리 원칙.
"""
from __future__ import annotations

from .critic_base import Critic, CriticResult, Verdict
from .c_legal import LegalCritic
from .c_carbon import CarbonCritic
from .c_safety import SafetyCritic
from .c_data import DataCritic
from .gate import (
    MANDATORY_SIGNAL_LEVELS,
    BatchDebateVerdict,
    CriticsGate,
    GateVerdict,
    summarize_dispatch_for_critics,
)

__all__ = [
    "Critic",
    "CriticResult",
    "Verdict",
    "LegalCritic",
    "CarbonCritic",
    "SafetyCritic",
    "DataCritic",
    "CriticsGate",
    "GateVerdict",
    "BatchDebateVerdict",
    "summarize_dispatch_for_critics",
    "MANDATORY_SIGNAL_LEVELS",
]
