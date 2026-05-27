"""rate_limit_policy SSOT 단위 테스트.

dataclass + slowapi 호환 string + 9 use-case 매개변수 검증.
"""

from __future__ import annotations

import pytest

from energy_contracts.rate_limit_policy import (
    RateLimitPolicy,
    format_slowapi,
    load_policy,
    slowapi_limit,
)


class TestFormatSlowapi:
    """RateLimitPolicy → slowapi string."""

    def test_minute_unit(self):
        p = RateLimitPolicy(requests=5, period_seconds=60)
        assert format_slowapi(p) == "5/minute"

    def test_hour_unit(self):
        p = RateLimitPolicy(requests=100, period_seconds=3600)
        assert format_slowapi(p) == "100/hour"

    def test_day_unit(self):
        p = RateLimitPolicy(requests=1000, period_seconds=86400)
        assert format_slowapi(p) == "1000/day"

    def test_second_unit(self):
        p = RateLimitPolicy(requests=10, period_seconds=1)
        assert format_slowapi(p) == "10/second"

    def test_custom_period(self):
        # 슬로우api 표준 단위 외 — fallback string
        p = RateLimitPolicy(requests=20, period_seconds=30)
        assert format_slowapi(p) == "20 per 30 seconds"


class TestLoadPolicy:
    """JSON schema 로드 + 9 use-case 매개변수 검증."""

    def test_auth_login(self):
        p = load_policy("auth_login")
        assert p.requests == 5
        assert p.period_seconds == 60
        assert "brute-force" in p.description

    def test_auth_session(self):
        p = load_policy("auth_session")
        assert p.requests == 60
        assert p.period_seconds == 60

    def test_public_default(self):
        p = load_policy("public_default")
        assert p.requests == 120
        assert p.period_seconds == 60

    def test_service_default(self):
        p = load_policy("service_default")
        assert p.requests == 60
        assert p.period_seconds == 60

    def test_write_normal(self):
        p = load_policy("write_normal")
        assert p.requests == 20
        assert p.period_seconds == 60

    def test_control_command(self):
        p = load_policy("control_command")
        assert p.requests == 10
        assert p.period_seconds == 60

    def test_expensive_compute(self):
        p = load_policy("expensive_compute")
        assert p.requests == 3
        assert p.period_seconds == 60

    def test_strict_read(self):
        p = load_policy("strict_read")
        assert p.requests == 5
        assert p.period_seconds == 60

    def test_webhook_inbound(self):
        p = load_policy("webhook_inbound")
        assert p.requests == 30
        assert p.period_seconds == 60

    def test_read_moderate(self):
        p = load_policy("read_moderate")
        assert p.requests == 30
        assert p.period_seconds == 60
        assert "표준 GET" in p.description

    def test_read_burst(self):
        p = load_policy("read_burst")
        assert p.requests == 200
        assert p.period_seconds == 60
        assert "폴링" in p.description or "HLS" in p.description

    def test_stream_realtime(self):
        p = load_policy("stream_realtime")
        assert p.requests == 600
        assert p.period_seconds == 60

    def test_daily_quota(self):
        p = load_policy("daily_quota")
        assert p.requests == 10
        assert p.period_seconds == 3600

    def test_unknown_use_case_raises(self):
        with pytest.raises(KeyError, match="unknown rate-limit use_case"):
            load_policy("nonexistent")


class TestSlowapiLimit:
    """one-shot helper for decorator usage."""

    def test_auth_login_string(self):
        assert slowapi_limit("auth_login") == "5/minute"

    def test_expensive_compute_string(self):
        assert slowapi_limit("expensive_compute") == "3/minute"

    def test_public_default_string(self):
        assert slowapi_limit("public_default") == "120/minute"

    def test_daily_quota_hour_unit(self):
        assert slowapi_limit("daily_quota") == "10/hour"

    def test_stream_realtime_string(self):
        assert slowapi_limit("stream_realtime") == "600/minute"

    def test_read_burst_string(self):
        assert slowapi_limit("read_burst") == "200/minute"

    def test_read_moderate_string(self):
        assert slowapi_limit("read_moderate") == "30/minute"


class TestParityBE3D:
    """be-3d 기존 데코레이터 값 보존 검증.

    sweep (2026-05-27):
        - auth/router.py login/register: 5/m  ← auth_login
        - auth/router.py me: 60/m            ← auth_session
        - shared/limiter.py default: 120/m   ← public_default
        - bot/kakao_webhook.py: 30/m         ← webhook_inbound
        - fire_safety/risk.py: 5/m × 4       ← strict_read
        - fire_safety/risk.py: 3/m × 1       ← expensive_compute
    """

    def test_auth_routes_parity(self):
        assert slowapi_limit("auth_login") == "5/minute"
        assert slowapi_limit("auth_session") == "60/minute"

    def test_default_parity(self):
        assert slowapi_limit("public_default") == "120/minute"

    def test_webhook_parity(self):
        assert slowapi_limit("webhook_inbound") == "30/minute"

    def test_fire_safety_parity(self):
        assert slowapi_limit("strict_read") == "5/minute"
        assert slowapi_limit("expensive_compute") == "3/minute"


class TestParityGB:
    """GB 기존 데코레이터 값 보존 검증.

    sweep (2026-05-27):
        - main.py default: 60/m              ← service_default
        - api/catalog.py: 5/m                ← strict_read
        - api/events.py: 20/m × 2            ← write_normal
        - api/venues.py: 20/m                ← write_normal
        - mqtt/router.py: 10/m × 2           ← control_command
        - mqtt/router.py: 5/m                ← strict_read
    """

    def test_service_default_parity(self):
        assert slowapi_limit("service_default") == "60/minute"

    def test_write_normal_parity(self):
        assert slowapi_limit("write_normal") == "20/minute"

    def test_control_command_parity(self):
        assert slowapi_limit("control_command") == "10/minute"

    def test_strict_read_parity(self):
        assert slowapi_limit("strict_read") == "5/minute"
