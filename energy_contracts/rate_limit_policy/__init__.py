"""Rate-limit policy — slowapi 호환 inbound HTTP rate-limit SSOT (Layer 1).

be-3d `src/shared/limiter.py` + per-route `@limiter.limit("N/minute")` 와
gridbridge `src/api/*.py` 의 분산된 `_limiter = Limiter(...)` 인스턴스를
본 SSOT 의 9 정책으로 통합한다.

설계:
- 정책 = 요청수 + 기간 + 설명 (정적 dataclass)
- slowapi 호환 string 생성 helper (`slowapi_limit()`) — 데코레이터 인자 직접 사용
- 키 추출 (IP / 사용자 ID 등) 은 호출자 책임 — 본 모듈은 정책만 SSOT

SSOT 위치: `myjob/docs/SSOT_GOVERNANCE.md` §9.5 사례 표.
"""
from __future__ import annotations

from .policy import (
    RateLimitPolicy,
    format_slowapi,
    load_policy,
    slowapi_limit,
)

__all__ = [
    "RateLimitPolicy",
    "format_slowapi",
    "load_policy",
    "slowapi_limit",
]
