"""C-Safety — HVAC·PMV·ESS·조명 interlock 위반 검출."""

from __future__ import annotations

import re
from typing import Any

from .critic_base import Critic, CriticResult


HVAC_SETPOINT_MIN_C = 18.0
HVAC_SETPOINT_MAX_C = 28.0
PMV_ABS_MAX = 0.5
ESS_SOC_MIN_PCT = 10.0
LIGHTING_MIN_PCT = 20.0

SETPOINT_PATTERN = re.compile(
    r"(?:냉방|난방|setpoint|HVAC|에어컨|히터).{0,20}?(\d{1,2}(?:\.\d)?)\s*°?C"
)
PMV_PATTERN = re.compile(r"PMV[^0-9-]*(-?\d+(?:\.\d+)?)")
SOC_PATTERN = re.compile(r"(?:SOC|ESS\s*SOC|배터리\s*잔량)[^0-9]*(\d+(?:\.\d+)?)\s*%")
LIGHT_PATTERN = re.compile(r"조명[^0-9]*(\d+(?:\.\d+)?)\s*%")


class SafetyCritic(Critic):
    name = "c_safety"

    def review(self, answer: str, context: dict[str, Any] | None = None) -> CriticResult:
        violations: list[dict[str, Any]] = []

        for m in SETPOINT_PATTERN.finditer(answer):
            val = float(m.group(1))
            if not (HVAC_SETPOINT_MIN_C <= val <= HVAC_SETPOINT_MAX_C):
                violations.append({
                    "rule": "hvac_setpoint_out_of_range",
                    "value_c": val,
                    "allowed": [HVAC_SETPOINT_MIN_C, HVAC_SETPOINT_MAX_C],
                })

        for m in PMV_PATTERN.finditer(answer):
            val = float(m.group(1))
            if abs(val) > PMV_ABS_MAX:
                violations.append({
                    "rule": "pmv_out_of_comfort",
                    "value": val,
                    "limit_abs": PMV_ABS_MAX,
                })

        for m in SOC_PATTERN.finditer(answer):
            val = float(m.group(1))
            if val < ESS_SOC_MIN_PCT:
                violations.append({
                    "rule": "ess_soc_below_floor",
                    "value_pct": val,
                    "floor_pct": ESS_SOC_MIN_PCT,
                })

        for m in LIGHT_PATTERN.finditer(answer):
            val = float(m.group(1))
            if val < LIGHTING_MIN_PCT:
                violations.append({
                    "rule": "lighting_below_floor",
                    "value_pct": val,
                    "floor_pct": LIGHTING_MIN_PCT,
                })

        return self._make_result(violations, notes="edge-agent interlocks 룰")
