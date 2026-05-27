"""Retry / Backoff policy — 도메인 횡단 SSOT (Layer 1).

지수 backoff delay 계산 + 선언적 정책 (4 use-case).

- be-3d `src/auth/backoff.py` 의 `_compute_delay` 와
  agents `src/ingestion/circuit_breaker.py` 의 `_compute_cooldown` 이
  같은 수학 커널(지수 증가 + 상한)을 중복 구현하던 것을 본 패키지로 통합.
- jitter 전략 4 종 (none/full/equal/decorrelated) — AWS Architecture Blog
  "Exponential Backoff and Jitter" (Marc Brooker, 2015) 표준 분류.
- `schemas/retry_policy.json` 의 use-case 4 종 (auth / external_api / mqtt / db) 를
  `load_policy(use_case)` 로 가져와 호출자 컨텍스트에 주입.

SSOT 위치: `myjob/docs/SSOT_GOVERNANCE.md` §9.5 사례 표.
"""
from __future__ import annotations

from .policy import (
    BackoffPolicy,
    JitterStrategy,
    compute_delay,
    load_policy,
)

__all__ = [
    "BackoffPolicy",
    "JitterStrategy",
    "compute_delay",
    "load_policy",
]
