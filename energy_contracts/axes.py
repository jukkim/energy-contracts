"""축 어휘·용도→원형 — EC 패키지를 import 하는 소비처(게이트웨이·AIROS)용 입구 (2026-09-28 일반화 G1).

규칙 본문은 ``rules_pure.py`` 한 벌이다(생성본에도 같은 원문이 실리고, 생성기 ``axis_tables`` 도 같은 함수를 부른다).
여기서는 스키마에서 표를 읽어 넘기기만 한다.
"""
from __future__ import annotations

from functools import lru_cache

from energy_contracts import load_schema
from energy_contracts.rules_pure import (ec_axis_encode, ec_axis_tables, ec_carbon_kg, ec_percentile,
                                         ec_usage_to_archetype)

__all__ = ["alias_index", "encode", "kbep_id", "usage_to_archetype", "usage_archetype_table", "percentile",
           "carbon_kg"]


@lru_cache(maxsize=1)
def _tables() -> dict:
    region = load_schema("region_codes")["default"]
    ems = load_schema("ems_strategies")["default"]
    return ec_axis_tables(load_schema("building_archetypes")["default"]["doe_buildings"],
                          region["simulation_cities"], region["hvac_types"],
                          ems["strategies"], ems.get("kbep_fast_path") or [])


def alias_index() -> dict[str, dict[str, str]]:
    return _tables()["index"]


def encode(kind: str, token: object) -> str:
    """토큰 → 정본 코드. 모르면 KeyError('AXIS_TOKEN_UNKNOWN …')."""
    return ec_axis_encode(kind, token, alias_index())


def kbep_id(kind: str, token: object) -> int:
    """토큰 → KBEP 정수 축. 전략이 fast-path 밖(M16~M22)이면 KeyError('KBEP_FAST_PATH_OUT …')."""
    code = encode(kind, token)
    ids = _tables()["kbep"][kind]
    if code not in ids:
        raise KeyError(f"KBEP_FAST_PATH_OUT: {kind} {code} 는 KBEP 정수 축에 없다")
    return ids[code]


@lru_cache(maxsize=1)
def usage_archetype_table() -> dict:
    return load_schema("building_usage_map")["default"]["usage_archetype"]


def usage_to_archetype(usage: object, gross_floor_area_m2: object = None, floors_above: object = None) -> dict:
    return ec_usage_to_archetype(usage, gross_floor_area_m2, usage_archetype_table(), floors_above)


def percentile(values, q: float):
    return ec_percentile(values, q)


def carbon_kg(fuel_kwh: dict) -> float:
    return ec_carbon_kg(fuel_kwh, load_schema("energy_units")["default"]["emission_factors_kr"])
