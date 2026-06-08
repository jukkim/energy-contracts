"""C-Carbon — 배출계수 SSOT 정합 (ENERGY_SSOT + CARBON_EMISSION_FACTORS.yaml)."""

from __future__ import annotations

import re
from typing import Any

from .critic_base import Critic, CriticResult


SSOT_FACTORS_KGCO2_PER_KWH = {
    "electricity_kr_2023": 0.4173,
    "natural_gas_kr": 0.202,
    "district_heating_kr": 0.178,
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

        return self._make_result(
            violations,
            fail_threshold=1,
            notes="CARBON_EMISSION_FACTORS.yaml 정합 — 1 건만 어긋나도 FAIL (audit 강화, 2026-05-27)",
        )
