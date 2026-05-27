"""ESG Scope 1/2/3 composer — 도메인 횡단 SSOT (Layer 1).

GB `src/scope/calculator.py::calculate_scope` 와
be-3d `src/simulation/scope_emissions.py::calculate_all_scopes` 가
중복 구현하던 Scope 1/2/3 composer 를 본 패키지로 통합.

설계:
- `ScopeInputs`  — 건물 데이터 (area, kWh/m² × 3, manual_overrides)
- `ScopeFactors` — 모든 factor 사전 lookup 결과 (호출자 책임)
- `compose_scope(inputs, factors) -> ScopeBreakdown` — 순수 함수 composer
- `embodied_key(structure, vintage)` — 구조×연대 sub_key 결정 (한국어 + 영문)

호출자 (GB/be-3d) 의 책임:
- DB / 캐시에서 factor lookup → ScopeFactors dataclass populate
- standard ("kr"/"eu") / year 분기 → 적절한 factor 주입
- response shape 변환 (각 도메인 response model)

SSOT 위치: `myjob/docs/SSOT_GOVERNANCE.md` §9.5 사례 표.
"""
from __future__ import annotations

from .composer import (
    EMBODIED_AMORTIZATION_YEARS,
    OVERRIDE_ALLOWED,
    ScopeBreakdown,
    ScopeFactors,
    ScopeInputs,
    compose_scope,
)
from .embodied_key import embodied_key

__all__ = [
    "EMBODIED_AMORTIZATION_YEARS",
    "OVERRIDE_ALLOWED",
    "ScopeBreakdown",
    "ScopeFactors",
    "ScopeInputs",
    "compose_scope",
    "embodied_key",
]
