"""Frontier Planner Gateway — **결정론 계획군 P0~P5 + 결정론 평가기** (ADR-018).

## 무엇을 만들고 무엇을 안 만드나

SSOT §4.1 은 이렇게 정한다:

    MissionIntentSnapshot → **deterministic plan templates P0~P5**
    → Frontier generation runs → schema/capability validation
    → canonical normalization/fingerprint → **deterministic evaluation**
    → immutable PlanRevision + content_hash

⚠ **LLM 을 부르지 않는다.** §6.2 가 *"Frontier AI 는 이 계획군을 대체하지 않고
확장·수정 후보를 제안한다"* 고 못 박았다 — 즉 **뼈대는 결정론 템플릿**이고
생성형은 그 위의 선택지다. 그래서 이 모듈은 템플릿과 평가기까지만 책임지고,
LLM 후보는 `extra_candidates` 로 **받아서 섞을 뿐** 만들지 않는다.

이렇게 하면 결선이 생성기 없이도 돌고(=pinned replay), 생성기가 붙으면
같은 평가기가 그 후보까지 함께 심사한다.

## 왜 평가기가 결정론이어야 하나

같은 후보 묶음에서 매번 다른 답이 나오면 **어제 승인한 계획이 오늘 다른 뜻**이
된다. 심사에서 "다시 돌려 보세요" 를 받으면 그 자리에서 무너진다.
그래서 점수는 순수 함수이고, 결과는 `decision_fingerprint` 로 못 박는다.

## 보호시설은 점수가 아니라 **관문**이다

보호 대상을 감점으로 다루면 이득이 크면 넘어간다. 여기서는 **후보 자체를
탈락**시킨다(`disqualified`). §11.1 40~62초의 *"최대확보안이 보호·rebound 조건으로
탈락"* 이 그 장면이다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from energy_contracts.frontier_fingerprint import (
    candidate_fingerprint, decision_fingerprint, generation_envelope)

#: §6.2 기본 계획군. 이름과 뜻을 여기 한 곳에만 둔다.
PLAN_TEMPLATES: dict[str, dict[str, Any]] = {
    "P0": {"label": "safe baseline / 비례 배분", "shed_ratio": 0.05,
           "comfort_band_c": 0.5, "uses_protected": False, "rebound_risk": 0.05},
    "P1": {"label": "comfort-first", "shed_ratio": 0.08,
           "comfort_band_c": 0.3, "uses_protected": False, "rebound_risk": 0.10},
    "P2": {"label": "lowest-cost / 비용우선", "shed_ratio": 0.18,
           "comfort_band_c": 1.2, "uses_protected": False, "rebound_risk": 0.35},
    "P3": {"label": "carbon-first", "shed_ratio": 0.15,
           "comfort_band_c": 1.0, "uses_protected": False, "rebound_risk": 0.25},
    "P4": {"label": "DR reliability / 최대확보", "shed_ratio": 0.32,
           "comfort_band_c": 1.8, "uses_protected": True, "rebound_risk": 0.55},
    "P5": {"label": "robust-balanced", "shed_ratio": 0.20,
           "comfort_band_c": 0.8, "uses_protected": False, "rebound_risk": 0.20},
}

#: 관문 — 넘으면 **탈락**이지 감점이 아니다.
REBOUND_LIMIT = 0.40
EVALUATOR_VERSION = "planner-1.0.0"


@dataclass(frozen=True)
class Snapshot:
    """MissionIntentSnapshot 최소형 — 계획을 정하는 **사실**만."""
    snapshot_id: str
    target_kw: float
    total_capacity_kw: float
    protected_ven_ids: tuple[str, ...] = ()
    objective_version: str = "obj-1.0"
    policy_version: str = "pol-1.0"
    #: 계량·요금 축(비용 점수용). 없으면 0 으로 두지 않고 **None** 이다 —
    #: 0 은 "공짜" 라는 뜻이고 부재와 다르다.
    unit_cost_krw_per_kwh: float | None = None
    extra_candidates: tuple[dict, ...] = field(default_factory=tuple)


def build_candidates(snap: Snapshot) -> list[dict]:
    """P0~P5 + (있으면) 외부 후보. **순서는 템플릿 키 정렬로 고정.**"""
    out: list[dict] = []
    for key in sorted(PLAN_TEMPLATES):
        t = PLAN_TEMPLATES[key]
        shed_kw = round(snap.total_capacity_kw * t["shed_ratio"], 1)
        out.append({
            "template": key, "label": t["label"],
            "shed_kw": shed_kw,
            "meets_target": shed_kw >= snap.target_kw,
            "comfort_band_c": t["comfort_band_c"],
            "rebound_risk": t["rebound_risk"],
            # 보호시설을 건드리는가 — 관문 입력
            "touches_protected": bool(t["uses_protected"] and snap.protected_ven_ids),
            "protected_ven_ids": list(snap.protected_ven_ids)
            if t["uses_protected"] else [],
        })
    out.extend(dict(c) for c in snap.extra_candidates)
    return out


def screen(candidates: list[dict]) -> list[dict]:
    """관문 — **탈락 사유를 이름으로 남긴다.** 조용히 빼면 왜 없는지 못 묻는다."""
    for c in candidates:
        why = []
        # ⚠ **목표 미달은 감점이 아니라 탈락이다.** 처음엔 감점(-60)으로 뒀더니
        #   절감이 적어 감점도 적은 **P0(safe baseline)가 1등**을 했다 —
        #   목표를 못 채우는 것이 "가장 좋은 계획" 으로 뽑히는 상태였다.
        #   목표를 못 채우면 그건 계획이 아니다.
        if not c.get("meets_target"):
            why.append("목표 미달 — 계획이 아니다")
        if c.get("touches_protected"):
            why.append("보호시설을 대상에 넣는다")
        if float(c.get("rebound_risk", 0)) > REBOUND_LIMIT:
            why.append(f"복귀피크 위험 {c['rebound_risk']:.0%} > 한도 {REBOUND_LIMIT:.0%}")
        c["disqualified"] = bool(why)
        c["disqualified_why"] = why
    return candidates


def score(c: dict, snap: Snapshot) -> float:
    """결정론 점수 — **순수 함수.** 시각·난수·외부 상태를 안 본다.

    목표 충족 여부는 **여기서 안 본다** — 관문(`screen`)이 이미 걸렀다.
    남은 축은 쾌적 훼손·복귀피크·과잉 절감 비용이다.
    ⚠ 비용은 단가를 **알 때만** 센다. 모르면 0 점으로 채우지 않는다 —
      모르는 것을 좋은 쪽으로도 나쁜 쪽으로도 세지 않는다.
    """
    s = 100.0
    s -= float(c.get("comfort_band_c", 0)) * 12.0
    s -= float(c.get("rebound_risk", 0)) * 50.0
    if snap.unit_cost_krw_per_kwh is not None:
        # ⚠ **절감량 전체에 비용을 물리지 않는다.** 처음엔 그렇게 썼는데,
        #   절감이 목적인 계획에서 **절감할수록 감점**이 되어 순위가 뒤집혔다.
        #   비용은 **목표를 넘긴 만큼**(과잉 절감 = 낭비)에만 물린다.
        excess = max(0.0, float(c.get("shed_kw", 0)) - snap.target_kw)
        s -= excess * snap.unit_cost_krw_per_kwh * 0.001
    return round(s, 4)


def plan(snap: Snapshot, *, provider: str = "deterministic-template",
         model_id: str = "P0-P5", temperature: float = 0.0,
         seed: int | None = 0) -> dict:
    """스냅샷 → 후보 → 관문 → 점수 → 선택 → **결정 지문**.

    ⚠ 선택은 **살아남은 후보 중 최고점**이다. 탈락한 후보가 더 높은 점수를 가질 수
      있고(최대확보안이 그렇다), 그게 §11.1 40~62초의 장면이다 — 점수로는 이기는데
      관문에서 떨어진다.
    """
    cands = screen(build_candidates(snap))
    for c in cands:
        c["score"] = score(c, snap)
    alive = [c for c in cands if not c["disqualified"]]
    if not alive:
        raise ValueError("살아남은 후보가 없다 — 관문을 다 넘지 못했다")
    best = max(alive, key=lambda c: (c["score"], c["template"]))
    sel_index = cands.index(best)
    env = generation_envelope(
        snapshot_id=snap.snapshot_id, objective_version=snap.objective_version,
        policy_version=snap.policy_version, provider=provider, model_id=model_id,
        system_prompt="", tool_schema=sorted(PLAN_TEMPLATES),
        temperature=temperature, seed=seed,
        request_payload={"target_kw": snap.target_kw,
                         "capacity_kw": snap.total_capacity_kw,
                         "protected": sorted(snap.protected_ven_ids)})
    dec = decision_fingerprint(envelope=env, candidates=cands,
                               selected_index=sel_index,
                               evaluator_version=EVALUATOR_VERSION)
    return {
        "snapshot_id": snap.snapshot_id,
        "candidates": cands,
        "selected": best,
        "disqualified": [{"template": c["template"], "why": c["disqualified_why"]}
                         for c in cands if c["disqualified"]],
        "envelope": env,
        **dec,
        "candidate_fingerprints_by_template": {
            c.get("template", f"ext-{i}"): candidate_fingerprint(c)
            for i, c in enumerate(cands)},
    }
