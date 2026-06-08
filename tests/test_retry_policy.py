"""retry_policy SSOT 단위 테스트.

수학 커널 (compute_delay) + JSON schema 로드 (load_policy) + 4 use-case 매개변수 검증.
"""

from __future__ import annotations

import pytest

from energy_contracts.retry_policy import (
    BackoffPolicy,
    JitterStrategy,
    compute_delay,
    load_policy,
)


class TestComputeDelay:
    """수학 커널 — 지수 + threshold + 상한 + jitter."""

    def test_attempt_zero_returns_zero(self):
        p = BackoffPolicy(base_seconds=1.0, max_seconds=60.0)
        assert compute_delay(0, p) == 0.0

    def test_attempt_negative_returns_zero(self):
        p = BackoffPolicy(base_seconds=1.0, max_seconds=60.0)
        assert compute_delay(-5, p) == 0.0

    def test_attempt_below_threshold_returns_zero(self):
        # threshold=5, attempt 1~5 → 무료
        p = BackoffPolicy(base_seconds=1.0, max_seconds=60.0, threshold_attempts=5)
        for attempt in range(1, 6):
            assert compute_delay(attempt, p) == 0.0

    def test_attempt_above_threshold_starts_at_base(self):
        # threshold=5, attempt 6 → base_seconds (effective_attempt=1)
        p = BackoffPolicy(base_seconds=1.0, factor=2.0, max_seconds=60.0, threshold_attempts=5)
        assert compute_delay(6, p) == 1.0

    def test_exponential_doubling(self):
        # base=1, factor=2, no threshold → 1, 2, 4, 8, ...
        p = BackoffPolicy(base_seconds=1.0, factor=2.0, max_seconds=1000.0)
        assert compute_delay(1, p) == 1.0
        assert compute_delay(2, p) == 2.0
        assert compute_delay(3, p) == 4.0
        assert compute_delay(4, p) == 8.0

    def test_max_cap_enforced(self):
        # base=1, factor=2, max=10 → 1, 2, 4, 8, 10(cap), 10(cap), ...
        p = BackoffPolicy(base_seconds=1.0, factor=2.0, max_seconds=10.0)
        assert compute_delay(5, p) == 10.0  # raw=16, capped=10
        assert compute_delay(100, p) == 10.0  # overflow guard

    def test_overflow_guard_at_30_shift(self):
        # 2^31 만 안전 — shift > 30 일 때 max_seconds 반환
        p = BackoffPolicy(base_seconds=1.0, factor=2.0, max_seconds=1e9)
        # attempt 32 → effective=32, shift=31 → max_seconds
        assert compute_delay(40, p) == 1e9

    def test_zero_factor_returns_zero_raw(self):
        # factor=0 또는 base=0 → raw=0
        p = BackoffPolicy(base_seconds=0.0, factor=2.0, max_seconds=60.0)
        assert compute_delay(5, p) == 0.0

    def test_non_doubling_factor(self):
        # factor=3.0 — tripling
        p = BackoffPolicy(base_seconds=1.0, factor=3.0, max_seconds=1000.0)
        assert compute_delay(1, p) == 1.0
        assert compute_delay(2, p) == 3.0
        assert compute_delay(3, p) == 9.0

    def test_jitter_none_is_deterministic(self):
        p = BackoffPolicy(
            base_seconds=1.0, factor=2.0, max_seconds=100.0, jitter=JitterStrategy.NONE,
        )
        for _ in range(10):
            assert compute_delay(5, p) == 16.0

    def test_jitter_full_uses_random_fn(self):
        # random_fn = midpoint → uniform(0, capped) midpoint = capped/2
        p = BackoffPolicy(
            base_seconds=1.0, factor=2.0, max_seconds=100.0, jitter=JitterStrategy.FULL,
        )
        midpoint = lambda a, b: (a + b) / 2.0
        # attempt=5 → capped=16, midpoint(0, 16) = 8
        assert compute_delay(5, p, random_fn=midpoint) == 8.0

    def test_jitter_equal_uses_random_fn(self):
        # equal: capped/2 + uniform(0, capped/2)
        p = BackoffPolicy(
            base_seconds=1.0, factor=2.0, max_seconds=100.0, jitter=JitterStrategy.EQUAL,
        )
        midpoint = lambda a, b: (a + b) / 2.0
        # attempt=5 → capped=16, 8 + midpoint(0,8) = 8 + 4 = 12
        assert compute_delay(5, p, random_fn=midpoint) == 12.0

    def test_jitter_decorrelated_uses_random_fn(self):
        # decorrelated: uniform(base, capped * 3), capped at max_seconds
        p = BackoffPolicy(
            base_seconds=1.0,
            factor=2.0,
            max_seconds=100.0,
            jitter=JitterStrategy.DECORRELATED,
        )
        midpoint = lambda a, b: (a + b) / 2.0
        # attempt=5 → capped=16, midpoint(1, 48) = 24.5, < max(100) → 24.5
        assert compute_delay(5, p, random_fn=midpoint) == 24.5

    def test_jitter_decorrelated_caps_at_max(self):
        # decorrelated 결과가 max_seconds 를 넘으면 max 로 잘림
        p = BackoffPolicy(
            base_seconds=1.0,
            factor=2.0,
            max_seconds=10.0,
            jitter=JitterStrategy.DECORRELATED,
        )
        # raw uniform 결과를 max 보다 크게 반환하는 fake
        big = lambda a, b: 1e6
        assert compute_delay(5, p, random_fn=big) == 10.0


class TestLoadPolicy:
    """JSON schema 로드 + 4 use-case 매개변수 검증."""

    def test_auth_policy(self):
        p = load_policy("auth")
        assert p.base_seconds == 1.0
        assert p.factor == 2.0
        assert p.max_seconds == 3600.0
        assert p.threshold_attempts == 5
        assert p.window_seconds == 300.0
        assert p.jitter == JitterStrategy.NONE

    def test_external_api_policy(self):
        p = load_policy("external_api")
        assert p.base_seconds == 1800.0
        assert p.factor == 2.0
        assert p.max_seconds == 86400.0
        assert p.threshold_attempts == 0
        assert p.window_seconds == 300.0
        assert p.jitter == JitterStrategy.NONE

    def test_mqtt_reconnect_policy(self):
        p = load_policy("mqtt_reconnect")
        assert p.base_seconds == 1.0
        assert p.max_seconds == 60.0
        assert p.jitter == JitterStrategy.EQUAL

    def test_db_policy(self):
        p = load_policy("db")
        assert p.base_seconds == 0.1
        assert p.max_seconds == 5.0
        assert p.jitter == JitterStrategy.FULL

    def test_unknown_use_case_raises(self):
        with pytest.raises(KeyError, match="unknown retry use_case"):
            load_policy("nonexistent_case")


class TestParitySwapAuth:
    """be-3d auth/backoff.py 의 _compute_delay 동작 보존 검증.

    이전 동작 (be-3d 1a853d2 시점):
        excess = count - 5
        if excess <= 0: return 0
        return min(1 << (excess - 1), 3600)
    """

    def test_be3d_auth_parity(self):
        p = load_policy("auth")
        # count <= 5 → 0
        for count in range(0, 6):
            assert compute_delay(count, p) == 0.0
        # count=6 → 1, 7→2, 8→4, 9→8, ...
        assert compute_delay(6, p) == 1.0
        assert compute_delay(7, p) == 2.0
        assert compute_delay(8, p) == 4.0
        assert compute_delay(9, p) == 8.0
        assert compute_delay(10, p) == 16.0
        # 큰 count 는 3600 상한
        assert compute_delay(50, p) == 3600.0


class TestParitySwapCircuitBreaker:
    """agents circuit_breaker.py 의 _compute_cooldown 동작 보존 검증.

    이전 동작:
        if repeats <= 1: return base
        cap_multiplier = MAX // base
        multiplier = min(2^(repeats-1), cap_multiplier)
        return min(base * multiplier, MAX)
    """

    def test_agents_cb_parity_first_open(self):
        # repeats=1 → base (1800s = 30min)
        p = load_policy("external_api")
        # 본 SSOT 는 attempt=1 → base. agents 의 repeats=1 와 매핑.
        assert compute_delay(1, p) == 1800.0

    def test_agents_cb_parity_doubling(self):
        p = load_policy("external_api")
        # repeats=2 → 3600 (1h)
        assert compute_delay(2, p) == 3600.0
        # repeats=3 → 7200 (2h)
        assert compute_delay(3, p) == 7200.0
        # repeats=4 → 14400 (4h)
        assert compute_delay(4, p) == 14400.0

    def test_agents_cb_parity_caps_at_24h(self):
        p = load_policy("external_api")
        # 큰 repeats → 86400 (24h) 상한
        assert compute_delay(20, p) == 86400.0


class TestRobustnessHunterRound:
    """사냥꾼 라운드 LOW (2026-06-08): overflow 가드 + decorrelated 하한 클램프."""

    def test_huge_factor_no_overflow(self):
        # 거대 factor 에서도 OverflowError 없이 max_seconds 로 포화
        p = BackoffPolicy(base_seconds=1.0, factor=1e308, max_seconds=1e9)
        d = compute_delay(3, p)
        assert d == 1e9

    def test_decorrelated_base_gt_max_clamped(self):
        # base>max 오설정 — 하한이 max 를 넘지 않아 jitter 가 무효화되지 않음
        p = BackoffPolicy(
            base_seconds=10.0, factor=2.0, max_seconds=5.0,
            jitter=JitterStrategy.DECORRELATED,
        )
        # rng 하한이 capped(=5)로 클램프되므로 rng(5, 15) 범위에서 동작
        lo_seen = compute_delay(1, p, random_fn=lambda a, b: a)
        assert lo_seen == 5.0  # min(max=5, rng 하한 5)
        hi_seen = compute_delay(1, p, random_fn=lambda a, b: b)
        assert hi_seen == 5.0  # min(max=5, 큰 값) = 5
