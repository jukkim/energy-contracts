"""C-Carbon — 배출계수 SSOT 정합 (ENERGY_SSOT + CARBON_EMISSION_FACTORS.yaml)."""

from __future__ import annotations

import re
from typing import Any

from .critic_base import Critic, CriticResult


SSOT_FACTORS_KGCO2_PER_KWH = {
    "electricity_kr_2023": 0.4173,
    "natural_gas_kr": 0.2036,
    "district_heating_kr": 0.1260,  # 수도권 2024 (ENERGY_SSOT v1.13 §1, 구 0.178 = SSOT 미반영 drift)
}

PE_FACTOR_KR = {
    "electricity": 2.75,
    "district_heating": 0.728,
    "natural_gas": 1.1,
}

FACTOR_PATTERN = re.compile(
    # 사냥꾼 라운드 M2 (2026-06-08): val 그룹이 \d+\.\d{2,4} 로 소수 2~4자리만 매칭하면
    #   '0.9'(1자리)·'5'(정수)·'0.41730'(5자리) 같은 명백한 오류 배출계수가 검사 누락
    #   (fail-open). \d+(?:\.\d+)? 로 정수/임의 소수 자리를 모두 캡처 → rel_err 비교가
    #   정상 동작 (합법값 0.4173 은 rel_err≈0 이라 false-positive 없음).
    r"(?P<src>전력|전기|가스|지역난방|district heating|electricity|natural gas)"
    r".{0,40}?(?P<val>\d+(?:\.\d+)?)\s*(?:kgCO2|kgCO2eq|kg\s*CO2)"
)

FACTOR_TOL_REL = 0.05

# 과대주장(overclaim) 게이트 — 주장 절감률이 독립 근거의 1.25배 초과 시 위반.
OVERCLAIM_MULTIPLIER = 1.25
# 절감률 단독 비현실 상한(독립 근거 무관).
IMPLAUSIBLE_REDUCTION = 0.5


def _as_rate(v: Any) -> float | None:
    """context 수치 → float rate. None/빈값/파싱불가 → None (독립값 '부재'를 0 과 구분).

    None 반환이 핵심: known_rate 부재 시 0 이나 claimed 로 대체하지 않고 검사 자체를
    skip 해야 self-reference(죽은 게이트)를 만들지 않는다.
    """
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _canon_source(s: str) -> str | None:
    s_lower = s.lower()
    if s in {"전력", "전기"} or "electricity" in s_lower:
        return "electricity_kr_2023"
    if s == "가스" or "natural gas" in s_lower:
        return "natural_gas_kr"
    if s == "지역난방" or "district heating" in s_lower:
        return "district_heating_kr"
    return None


class CarbonCritic(Critic):
    name = "c_carbon"

    def review(self, answer: str, context: dict[str, Any] | None = None) -> CriticResult:
        violations: list[dict[str, Any]] = []

        for m in FACTOR_PATTERN.finditer(answer):
            src = m.group("src")
            val = float(m.group("val"))
            key = _canon_source(src)
            if not key:
                continue
            ssot = SSOT_FACTORS_KGCO2_PER_KWH[key]
            rel_err = abs(val - ssot) / ssot
            if rel_err > FACTOR_TOL_REL:
                violations.append({
                    "rule": "factor_mismatch",
                    "source": key,
                    "answer_value": val,
                    "ssot_value": ssot,
                    "relative_error": round(rel_err, 4),
                })

        if "0.4747" in answer or "0.4781" in answer:
            violations.append({
                "rule": "outdated_electricity_factor",
                "reason": "2025.12 갱신 — 0.4173 권장 (단년도 확정)",
            })

        # ── 과대주장 게이트 — claimed vs known 독립 출처 (P2-c, 2026-06-17) ──────────
        # claimed_reduction_pct = 에이전트/LLM 주장 절감률, known_rate = **독립 ground
        # truth**(E+ 시뮬·전략 코드 stub). 두 값이 같은 출처에서 파생되면(self-reference)
        # claimed>known×1.25 가 영구히 거짓이 되어 게이트가 죽는다. 따라서:
        #   ① claimed/known 은 context 의 **별개 키**에서만 읽는다(상호 대체 금지).
        #   ② known 부재(None) 시 claimed 로 메우지 않고 overclaim 검사를 **skip** 한다.
        # 독립성 보장 책임은 producer(agentleague service._make_claim: known=E+ 독립값,
        # claimed=LLM 파싱)에 있고, 본 Critic 은 그 분리를 무너뜨리지 않는 소비자다.
        # 정본: agentleague/docs/POLICY_LEVER_SOLVABILITY_AUDIT.md §6 P2-c / CB-01.
        ctx = context or {}
        claimed = _as_rate(ctx.get("claimed_reduction_pct"))
        known = _as_rate(ctx.get("known_rate"))
        if claimed is not None and known is not None and known > 0 and (
            claimed > known * OVERCLAIM_MULTIPLIER
        ):
            violations.append({
                "rule": "overclaim",
                "claimed_reduction_pct": round(claimed, 4),
                "known_rate": round(known, 4),
                "threshold": round(known * OVERCLAIM_MULTIPLIER, 4),
                "detail": f"주장 절감률 {claimed:.0%} > 독립 근거 {known:.0%}×{OVERCLAIM_MULTIPLIER}",
            })
        if claimed is not None and claimed > IMPLAUSIBLE_REDUCTION:
            violations.append({
                "rule": "implausible_reduction",
                "claimed_reduction_pct": round(claimed, 4),
                "detail": f"절감률 {claimed:.0%} 비현실적 (>{IMPLAUSIBLE_REDUCTION:.0%})",
            })

        return self._make_result(
            violations,
            fail_threshold=1,
            notes="CARBON_EMISSION_FACTORS.yaml 정합 — 1 건만 어긋나도 FAIL (audit 강화, 2026-05-27)",
        )
