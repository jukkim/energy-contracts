"""Backoff delay 계산 커널 + 정책 dataclass.

수학 커널: `raw = base * factor^(attempt-1)` capped at `max_seconds`.

attempt 의미:
- 0 → 0 (delay 없음 — caller 가 첫 시도 전에 호출하면 즉시 진행)
- 1 → base
- 2 → base * factor
- N → base * factor^(N-1), 단 max_seconds 상한

jitter 4 종 (AWS Brooker 2015 분류):
- "none"          — 결정적 (테스트·재현성)
- "full"          — uniform(0, capped)
- "equal"         — capped/2 + uniform(0, capped/2)
- "decorrelated"  — uniform(base, capped * 3), max_seconds 상한 (thundering herd 완화)

본 모듈은 **순수 수학 + 정책 dataclass** 만 제공한다. 상태 머신
(circuit breaker, IP fail counter 등) 은 호출자 책임. jitter 의 무작위
seed 도 호출자가 주입 가능 (`random_fn` 인자) — 테스트에서 결정성 확보.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from typing import Callable


class JitterStrategy(str, Enum):
    NONE = "none"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


@dataclass(frozen=True)
class BackoffPolicy:
    """선언적 backoff 정책 (use-case 별).

    Attributes:
        base_seconds: attempt=1 일 때 delay (초)
        factor: 지수 배율 (기본 2.0 — doubling)
        max_seconds: delay 상한 (초)
        threshold_attempts: 이 횟수 이하 attempt 는 delay=0 (free retry)
            예) auth use-case = 5 → 5회 까지는 무료, 6번째부터 backoff 시작
        window_seconds: 카운터 자연 소멸 윈도우 (초, optional).
            상태 머신 호출자가 사용 — 본 모듈은 참조만 (compute_delay 미사용).
        jitter: JitterStrategy.NONE / FULL / EQUAL / DECORRELATED

    schemas/retry_policy.json 의 4 use-case (auth / external_api / mqtt / db) 가
    load_policy() 로 본 dataclass 로 인스턴스화된다.
    """
    base_seconds: float
    factor: float = 2.0
    max_seconds: float = 3600.0
    threshold_attempts: int = 0
    window_seconds: float | None = None
    jitter: JitterStrategy = JitterStrategy.NONE


def compute_delay(
    attempt: int,
    policy: BackoffPolicy,
    *,
    random_fn: Callable[[float, float], float] | None = None,
) -> float:
    """attempt N → delay 초.

    Args:
        attempt: 시도 횟수 (0 이하 → 0 반환)
        policy: BackoffPolicy
        random_fn: jitter 용 uniform(a, b) 콜백. None 이면 random.uniform.
            결정적 테스트에서 lambda a, b: (a + b) / 2 같은 fake 주입.

    Returns:
        delay 초 (float, 음수 없음).
    """
    if attempt <= 0:
        return 0.0
    if attempt <= policy.threshold_attempts:
        return 0.0

    effective_attempt = attempt - policy.threshold_attempts

    if policy.factor <= 0 or policy.base_seconds <= 0:
        raw = 0.0
    elif effective_attempt - 1 > 30:
        raw = policy.max_seconds
    else:
        # 사냥꾼 라운드 LOW (2026-06-08): 가드가 지수 '횟수'만 보고 factor 크기를 무시해
        #   거대 factor(상한 미설정 schema)에서 OverflowError 가능 → max_seconds 로 포화.
        try:
            raw = policy.base_seconds * (policy.factor ** (effective_attempt - 1))
        except OverflowError:
            raw = policy.max_seconds

    capped = min(raw, policy.max_seconds)

    if policy.jitter == JitterStrategy.NONE:
        return capped

    rng = random_fn if random_fn is not None else random.uniform
    if policy.jitter == JitterStrategy.FULL:
        return rng(0.0, capped)
    if policy.jitter == JitterStrategy.EQUAL:
        half = capped / 2.0
        return half + rng(0.0, half)
    if policy.jitter == JitterStrategy.DECORRELATED:
        # 사냥꾼 라운드 LOW (2026-06-08): base_seconds>capped(=max) 오설정 시 rng 하한이
        #   max 를 넘어 항상 max 로 포화(jitter 무효) → 하한을 capped 로 클램프.
        lo = min(policy.base_seconds, capped)
        return min(policy.max_seconds, rng(lo, capped * 3.0))
    return capped


def load_policy(use_case: str) -> BackoffPolicy:
    """schemas/retry_policy.json 의 use-case → BackoffPolicy.

    Args:
        use_case: "auth" | "external_api" | "mqtt_reconnect" | "db"

    Raises:
        KeyError: 알 수 없는 use_case
        FileNotFoundError: schema 파일 없음 (패키지 손상)
    """
    schema_text = (
        resources.files("energy_contracts.schemas")
        .joinpath("retry_policy.json")
        .read_text(encoding="utf-8")
    )
    data = json.loads(schema_text)
    cases = data.get("use_cases", {})
    if use_case not in cases:
        raise KeyError(
            f"unknown retry use_case: {use_case!r} "
            f"(available: {sorted(cases)})"
        )
    cfg = cases[use_case]
    return BackoffPolicy(
        base_seconds=float(cfg["base_seconds"]),
        factor=float(cfg.get("factor", 2.0)),
        max_seconds=float(cfg["max_seconds"]),
        threshold_attempts=int(cfg.get("threshold_attempts", 0)),
        window_seconds=(
            float(cfg["window_seconds"]) if "window_seconds" in cfg else None
        ),
        jitter=JitterStrategy(cfg.get("jitter", "none")),
    )
