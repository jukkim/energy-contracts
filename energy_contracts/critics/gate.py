"""CriticsGate — 4 종 Critic 조합 + 실시간 verdict + 사후 batch debate.

도메인 중립 게이트 조합자. 호출자가 도메인 컨텍스트 (DR / EMS / ESG 등) 를
이벤트 dict 로 주입하고, gate 가 이를 한국어 요약 텍스트로 변환해 critics 에 전달.

설계:
- Critics 는 같은 패키지의 4 종 (Layer 1, 룰 기반, 외부 의존 0)
- 입력: dispatch event dict → 한국어 요약 텍스트로 변환 → Critic.review(text)
  - Safety: setpoint / SOC / PMV / 조명 regex 탐지
  - Data:   그룹/멤버 이름에 NDA fingerprint (한수원/IITP/...)
  - Legal:  mandatory 발령의 법령 인용 정확성
- 실시간 verdict: FAIL → 호출자 측에서 차단, WARN → flag 추가 후 진행, PASS → 그대로
- Cache: 이벤트 signature (group_id, target_kw 1 자리 반올림, mandatory, source) 키
  → 같은 정책 반복 dispatch 시 재평가 skip
- Carbon Critic 은 실 outcome (avoided CO2) 필요 → batch 사후 토론에서만 적용

SSOT 위치: `myjob/docs/SSOT_GOVERNANCE.md` §9.5 — DR Critics 사례.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .c_carbon import CarbonCritic
from .c_data import DataCritic
from .c_legal import LegalCritic
from .c_safety import SafetyCritic
from .critic_base import CriticResult, Verdict

logger = logging.getLogger(__name__)


# DR signal_level 중 의무 발령 (Legal Critic 의 mandatory 컨텍스트 보강 대상).
# SSOT: `dr_event.json` signal_level enum 의 부분집합.
# 사냥꾼 root-cause M3 (2026-05-27) — GB local `_MANDATORY_SIGNALS` 분리 해소.
MANDATORY_SIGNAL_LEVELS: frozenset[str] = frozenset({"HIGH", "EMERGENCY"})


@dataclass
class GateVerdict:
    """3 종 Critic 종합 결과."""
    decision: str  # "pass" | "warn" | "block"
    results: list[CriticResult] = field(default_factory=list)
    cache_hit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "results": [r.to_dict() for r in self.results],
            "cache_hit": self.cache_hit,
        }


@dataclass
class BatchDebateVerdict:
    """4 종 Critic + judge_decision 종합 (사후 batch)."""
    judge_decision: str  # "pass" | "needs_review" | "fail"
    realtime_results: list[CriticResult] = field(default_factory=list)
    carbon_result: CriticResult | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "judge_decision": self.judge_decision,
            "realtime_results": [r.to_dict() for r in self.realtime_results],
            "carbon_result": self.carbon_result.to_dict() if self.carbon_result else None,
            "notes": self.notes,
        }


def _setpoint_shift_estimate_c(reduction_kw: float, baseline_kw: float = 50.0) -> float:
    """kW 감축 → 냉방 setpoint 시프트 어림 (1°C 당 ~baseline_kw kW)."""
    if baseline_kw <= 0:
        return 0.0
    return reduction_kw / baseline_kw


def summarize_dispatch_for_critics(
    event: dict[str, Any],
    *,
    baseline_setpoint_c: float = 26.0,
) -> str:
    """dispatch event → 한국어 요약 텍스트.

    Critics 의 regex 패턴이 잡을 수 있도록 명시적 키워드 사용:
    - 'setpoint' / '냉방' / '난방' + 숫자°C
    - 'PMV' (있을 때만)
    - 'SOC' / '조명' (allocation meta 에 있을 때)
    - 그룹/멤버 식별자 (Data Critic 의 NDA fingerprint 검출용)
    """
    parts: list[str] = []
    group_id = event.get("group_id", "?")
    target_kw = float(event.get("target_kw", 0))
    source = event.get("source", "unknown")
    mandatory = event.get("mandatory", False)

    parts.append(f"DR 발령: 그룹 {group_id} 대상 {target_kw:.0f} kW 감축.")
    parts.append(f"발령 출처: {source}.")
    if mandatory:
        parts.append("의무 발령 (mandatory) — 녹색건축법에 따른 의무 대상.")

    meta = event.get("_decision_meta") or {}
    allocations = (
        event.get("allocations")
        or meta.get("allocations")
        or []
    )
    if allocations:
        for a in allocations[:8]:
            mb = a.get("member_id") or a.get("building_id") or "?"
            kw = float(a.get("reduction_kw") or a.get("allocated_kw") or 0)
            if kw <= 0:
                continue
            est_shift = _setpoint_shift_estimate_c(kw)
            est_setpoint = baseline_setpoint_c + est_shift
            parts.append(
                f"건물 {mb} 약 {kw:.0f} kW 감축 → 냉방 setpoint {est_setpoint:.1f}°C 추정."
            )
            # 추가 안전 지표가 allocation 에 있으면 텍스트에 포함
            if "soc_pct" in a:
                parts.append(f"건물 {mb} ESS SOC {float(a['soc_pct']):.0f}% 유지.")
            if "lighting_pct" in a:
                parts.append(f"건물 {mb} 조명 {float(a['lighting_pct']):.0f}%.")
            if "pmv" in a:
                parts.append(f"건물 {mb} PMV {float(a['pmv']):.2f}.")
    else:
        # 평균 1 건물 추정 (그룹 N=10 가정) — 보수적 worst-case
        est_per_bldg = target_kw / 10.0
        est_shift = _setpoint_shift_estimate_c(est_per_bldg)
        est_setpoint = baseline_setpoint_c + est_shift
        parts.append(
            f"평균 건물 약 {est_per_bldg:.0f} kW 감축 → 냉방 setpoint {est_setpoint:.1f}°C 추정."
        )

    return " ".join(parts)


def _signature(event: dict[str, Any]) -> tuple:
    """이벤트 cache key — 정책-유사 이벤트는 같은 signature."""
    return (
        event.get("group_id", ""),
        round(float(event.get("target_kw", 0)), 0),
        bool(event.get("mandatory", False)),
        event.get("source", ""),
        # allocations 의 멤버 ID 집합 (set 순서 무관)
        tuple(sorted(
            a.get("member_id") or a.get("building_id") or ""
            for a in (event.get("allocations") or [])
        )),
    )


class CriticsGate:
    """실시간 dispatch Critic 게이트.

    한 인스턴스를 호출자 (orchestrator / GB dispatcher 등) 가 보유.
    tick 마다 dispatch 직전 `evaluate_dispatch()`, 사후 batch 는 `evaluate_batch_debate()`.
    """

    def __init__(self, cache_size: int = 256) -> None:
        self.safety = SafetyCritic()
        self.legal = LegalCritic()
        self.data = DataCritic()
        self._cache: dict[tuple, GateVerdict] = {}
        self._cache_size = cache_size

    def evaluate_dispatch(self, event: dict[str, Any]) -> GateVerdict:
        """3 종 Critic 평가 → pass/warn/block 결정."""
        sig = _signature(event)
        cached = self._cache.get(sig)
        if cached is not None:
            return GateVerdict(decision=cached.decision, results=cached.results, cache_hit=True)

        text = summarize_dispatch_for_critics(event)
        # Data Critic 은 disclose_mode 무관하게 NDA fingerprint 만 검사 (1 건 노출 = FAIL)
        r_safety = self.safety.review(text)
        r_legal = self.legal.review(text)
        r_data = self.data.review(text)
        results = [r_safety, r_legal, r_data]

        if any(r.verdict == Verdict.FAIL for r in results):
            decision = "block"
        elif any(r.verdict == Verdict.WARN for r in results):
            decision = "warn"
        else:
            decision = "pass"

        verdict = GateVerdict(decision=decision, results=results, cache_hit=False)

        # FIFO eviction — 메모리 누수 방지
        if len(self._cache) >= self._cache_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[sig] = verdict
        return verdict

    def evaluate_batch_debate(
        self,
        event: dict[str, Any],
        *,
        outcome: dict[str, Any] | None = None,
    ) -> BatchDebateVerdict:
        """사후 batch — Carbon Critic + 종합 judge_decision.

        outcome 에 실제 avoided_kwh / measured_co2 / emission_factor 가 들어오면
        Carbon Critic 이 그 텍스트로 배출계수 SSOT 정합 검증을 수행한다.

        outcome=None 인 경우 Carbon Critic 은 **건너뛴다** — dispatch event 만으로는
        배출계수 컨텍스트가 결핍되어 거의 항상 false-pass 가 나오기 때문 (사냥꾼
        root-cause M2 보고, 2026-05-27). 이때 judge_decision 은 realtime 3 종
        결과만으로 산출하고 `carbon_result=None` 으로 반환한다.
        """
        # realtime 3 종 (cache hit 가능)
        rt = self.evaluate_dispatch(event)

        if outcome is None:
            # outcome 미주입 — Carbon Critic skip (M2 false-pass 방지)
            if any(r.verdict == Verdict.FAIL for r in rt.results):
                judge = "fail"
            elif any(r.verdict == Verdict.WARN for r in rt.results):
                judge = "needs_review"
            else:
                judge = "pass"
            return BatchDebateVerdict(
                judge_decision=judge,
                realtime_results=rt.results,
                carbon_result=None,
                notes=(
                    "outcome 미주입 — Carbon skip (cache hit)"
                    if rt.cache_hit
                    else "outcome 미주입 — Carbon skip"
                ),
            )

        # outcome 있음 — Carbon Critic 실행 (배출계수 정합 검증)
        carbon_text = summarize_dispatch_for_critics(event)
        ef = outcome.get("emission_factor_kgco2_per_kwh")
        src = outcome.get("source_type", "전력")
        avoided_kwh = outcome.get("avoided_kwh")
        if ef is not None:
            carbon_text += f" 적용 배출계수: {src} {float(ef):.4f} kgCO2/kWh."
        if avoided_kwh is not None:
            carbon_text += f" 실측 절감량 {float(avoided_kwh):.1f} kWh."
        r_carbon = CarbonCritic().review(carbon_text)

        # judge_decision 합의 룰 (4 종 종합)
        all_results = [*rt.results, r_carbon]
        if any(r.verdict == Verdict.FAIL for r in all_results):
            judge = "fail"
        elif any(r.verdict == Verdict.WARN for r in all_results):
            judge = "needs_review"
        else:
            judge = "pass"

        return BatchDebateVerdict(
            judge_decision=judge,
            realtime_results=rt.results,
            carbon_result=r_carbon,
            notes=("cache hit" if rt.cache_hit else "fresh evaluation"),
        )

    def clear_cache(self) -> None:
        """테스트/운영 리셋용."""
        self._cache.clear()
