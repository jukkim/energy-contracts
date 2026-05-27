"""Rate-limit policy dataclass + slowapi 호환 helper.

수학 / 키 추출 없음. **선언적 정책만** SSOT 로 둔다.

slowapi `@limiter.limit("5/minute")` 데코레이터는 module-load 시점에
string 인자가 필요 — 본 모듈의 `slowapi_limit(use_case)` 가 그 시점에
JSON schema 를 읽고 string 반환.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class RateLimitPolicy:
    """선언적 rate-limit 정책.

    Attributes:
        requests: window 안 허용 요청 수
        period_seconds: window 길이 (초). 60/3600/86400 외 값은 "{n} per {sec} seconds" 로 포맷.
        description: 정책 의도 (개발자 가이드 / OpenAPI 노출용)

    schemas/rate_limit_policy.json 의 use_case 별 객체가 본 dataclass 로 인스턴스화된다.
    """
    requests: int
    period_seconds: float
    description: str = ""


def format_slowapi(policy: RateLimitPolicy) -> str:
    """slowapi `@limiter.limit()` 호환 string 변환.

    슬로우api 표준 단위:
    - 1초 → "{n}/second"
    - 60초 → "{n}/minute"
    - 3600초 → "{n}/hour"
    - 86400초 → "{n}/day"
    - 그 외 → "{n} per {sec} seconds"
    """
    sec = policy.period_seconds
    if sec == 1:
        return f"{policy.requests}/second"
    if sec == 60:
        return f"{policy.requests}/minute"
    if sec == 3600:
        return f"{policy.requests}/hour"
    if sec == 86400:
        return f"{policy.requests}/day"
    return f"{policy.requests} per {int(sec)} seconds"


def load_policy(use_case: str) -> RateLimitPolicy:
    """schemas/rate_limit_policy.json 의 use-case → RateLimitPolicy.

    Args:
        use_case: "auth_login" | "auth_session" | "public_default" | "service_default"
                  | "write_normal" | "control_command" | "expensive_compute"
                  | "strict_read" | "webhook_inbound"

    Raises:
        KeyError: 알 수 없는 use_case
    """
    schema_text = (
        resources.files("energy_contracts.schemas")
        .joinpath("rate_limit_policy.json")
        .read_text(encoding="utf-8")
    )
    data = json.loads(schema_text)
    cases = data.get("use_cases", {})
    if use_case not in cases:
        raise KeyError(
            f"unknown rate-limit use_case: {use_case!r} "
            f"(available: {sorted(cases)})"
        )
    cfg = cases[use_case]
    return RateLimitPolicy(
        requests=int(cfg["requests"]),
        period_seconds=float(cfg["period_seconds"]),
        description=cfg.get("description", ""),
    )


def slowapi_limit(use_case: str) -> str:
    """`@limiter.limit(slowapi_limit("auth_login"))` 한 줄 사용 helper.

    내부적으로 `load_policy` + `format_slowapi` 조합. 모듈 import 시점에
    호출되어도 안전 (JSON 1 회 로드).
    """
    return format_slowapi(load_policy(use_case))
