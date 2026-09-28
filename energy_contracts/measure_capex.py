"""EMS 전략별 **가정** 설치비 — 식은 여기 한 곳(2026-09-28).

정본 값 = ``measure_cost_catalog.json#/default/ems_strategy_capex_assumption`` +
``measures[BEMS].capex_krw_per_m2`` + ``ems_strategies.json`` 의 복합 전략 구성.
소비처는 이 함수를 부른다 — 식을 다시 적으면 두 곳이 갈라진다.

    capex(M) = BEMS 단가 × |points(M)| / |point_universe|
    points(복합 전략) = 구성 전략 points 의 합집합

결과는 **가정**이다(evidence_grade=assumption, data_source=imputed, source='가정').
설비 본체(ESS·축열조·PV·ERV)는 넣지 않고 ``hardware_excluded`` 로 돌려준다.
"""
from __future__ import annotations

from . import load_schema


class StrategyCapexUnavailable(ValueError):
    """전략 코드가 정본에 없거나 제어점 정의가 없어 계산할 수 없다(이름 있는 거절)."""


def _sources() -> tuple[dict, dict]:
    catalog = load_schema("measure_cost_catalog")["default"]
    strategies = load_schema("ems_strategies")["default"]["strategies"]
    return catalog, strategies


def strategy_points(code: str, *, _catalog: dict | None = None, _strategies: dict | None = None) -> list[str]:
    """전략이 만지는 제어점(정렬). 복합 전략은 구성 전략의 합집합."""
    if _catalog is None or _strategies is None:
        _catalog, _strategies = _sources()
    block = _catalog["ems_strategy_capex_assumption"]
    singles = block["single_strategy_points"]
    meta = _strategies.get(code)
    if meta is None:
        raise StrategyCapexUnavailable(f"{code}: ems_strategies.json 에 없는 전략 코드")
    if meta["type"] == "combined":
        out: set[str] = set()
        for comp in meta["components"]:
            out.update(strategy_points(comp, _catalog=_catalog, _strategies=_strategies))
        return sorted(out)
    if code not in singles:
        raise StrategyCapexUnavailable(f"{code}: single_strategy_points 에 제어점 정의가 없다")
    universe = set(block["point_universe"])
    unknown = set(singles[code]) - universe
    if unknown:
        raise StrategyCapexUnavailable(f"{code}: point_universe 밖의 제어점 {sorted(unknown)}")
    return sorted(singles[code])


def strategy_capex(code: str) -> dict:
    """전략 하나의 가정 설치비(원/㎡)와 근거 봉투."""
    catalog, strategies = _sources()
    block = catalog["ems_strategy_capex_assumption"]
    bems = catalog["measures"][block["bems_measure_ref"]]
    points = strategy_points(code, _catalog=catalog, _strategies=strategies)
    n_universe = len(block["point_universe"])
    meta = strategies[code]
    components = meta["components"] if meta["type"] == "combined" else [code]
    hardware = {c: block["hardware_excluded"][c] for c in components if c in block["hardware_excluded"]}
    return {
        "strategy": code,
        "capex_krw_per_m2": bems["capex_krw_per_m2"] * len(points) / n_universe,
        "control_points": points,
        "point_share": f"{len(points)}/{n_universe}",
        "bems_capex_krw_per_m2": bems["capex_krw_per_m2"],
        "lifetime_yr": bems["lifetime_yr"],
        "hardware_excluded": hardware,
        "evidence_grade": block["evidence_grade"],
        "data_source": block["data_source"],
        "source": block["source"],
        "method": block["method"],
        "as_of": block["as_of"],
    }


def all_strategy_capex() -> dict[str, dict]:
    """정본 전략 전부(M00~M22)."""
    _, strategies = _sources()
    return {code: strategy_capex(code) for code in strategies}
