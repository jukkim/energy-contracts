"""식별자·행정구역 승계 공용 함수 (2026-09-28 일반화 G1).

정본 = 스키마 두 곳 — 이 모듈은 값을 들지 않고 읽기만 한다.
  * 식별자 정규식: ``common.json`` ``$defs`` (BuildingMgmtNo·ParcelId·AirAssetId·SigunguCode …)
  * 폐지·개편 승계: ``region_codes.json#default.admin_succession`` (be-3d region-resolver-table-v1 과 같은 원천)

왜 있나: 25자리 건물번호 → 필지 변환이 네 벌(be-3d 정본·AIROS·Studio·게이트웨이 ``ref[:19]``)이었고 게이트웨이 것만
강원·전북 옛 시도코드(42·45)를 승계코드(51·52)로 바꾸지 않았다. "번호가 이 필지 위에 있나" 판정도 네 벌·규칙 둘이었다
(게이트웨이는 ``[5:19]`` 만 견줘 시군구를 보지 않았다). AIR 번호 정규식은 다섯 저장소 15곳 이상이었다.

⚠ 광주·전남 통합 코드(12 ↔ 29/46)의 필지 짝은 ingestion-worker ``silver.sigungu_code_map``(DB)이 정본이라 여기 없다 —
   be-3d ``parcel_code.mart_parcel_id`` 가 맡는다. 이 모듈의 ``building_on_parcel`` 은 시도 승계까지만 본다.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

from energy_contracts import load_schema

__all__ = [
    "pattern", "matches", "admin_succession", "current_region_code", "current_parcel_id",
    "parcel_of_building", "building_on_parcel", "air_asset_kind", "air_asset_kinds",
]


@lru_cache(maxsize=1)
def _patterns() -> dict[str, "re.Pattern[str]"]:
    defs = load_schema("common").get("$defs", {})
    return {name: re.compile(node["pattern"]) for name, node in defs.items()
            if isinstance(node, dict) and node.get("pattern")}


def pattern(name: str) -> "re.Pattern[str]":
    """정본 정규식(컴파일). 모르는 이름은 KeyError — 빈 정규식으로 통과시키지 않는다."""
    pats = _patterns()
    if name not in pats:
        raise KeyError(f"common.json $defs 에 식별자 {name!r} 가 없다 (있는 것: {sorted(pats)})")
    return pats[name]


def matches(name: str, value: object) -> bool:
    return isinstance(value, str) and pattern(name).fullmatch(value) is not None


@lru_cache(maxsize=1)
def admin_succession() -> dict:
    return load_schema("region_codes")["default"]["admin_succession"]


def current_region_code(code: Optional[str]) -> Optional[str]:
    """2·5·10자리 행정 코드 → 현행 코드. ① 시도 접두 교체 ② 1:1 폐지 시군구(5자리 앞부분). split 시군구는
    동을 알아야 하므로 그대로 둔다(추측하지 않는다). 모양이 틀리면 None."""
    if not isinstance(code, str) or not code.isdigit() or len(code) not in (2, 5, 10):
        return None
    s = admin_succession()
    succ = s["sido_successor"].get(code[:2])
    if succ:
        code = succ + code[2:]
    if len(code) >= 5:
        sgg = s["sigungu_successor"].get(code[:5])
        if sgg:
            code = sgg + code[5:]
    return code


def current_parcel_id(pnu: Optional[str]) -> Optional[str]:
    """19자리 필지 → 시도 승계 코드의 필지(be-3d parcel_code.current_parcel_id 와 같은 규칙). 모양이 틀리면 None.

    시군구 1:1 폐지 승계는 필지에 적용하지 않는다 — 폐지 코드 필지는 동 번호까지 바뀐다(동 번역표가 be-3d 에 있다)."""
    if not matches("ParcelId", pnu):
        return None
    succ = admin_succession()["sido_successor"].get(pnu[:2])
    return succ + pnu[2:] if succ else pnu


def parcel_of_building(number: Optional[str]) -> Optional[str]:
    """25자리 건물관리번호 → 그 건물이 선 필지(승계 코드). ``[:19]`` 리터럴 대신 이것을 쓴다."""
    if not matches("BuildingMgmtNo", number):
        return None
    return current_parcel_id(number[:19])


def building_on_parcel(number: Optional[str], pnu: Optional[str]) -> bool:
    """건물번호가 이 필지 위의 건물인가 — 19자리 **전체**를 승계 코드로 견준다(시군구 5자리를 빼지 않는다)."""
    own = parcel_of_building(number)
    other = current_parcel_id(pnu)
    return own is not None and other is not None and own == other


@lru_cache(maxsize=1)
def air_asset_kinds() -> dict[str, dict]:
    return load_schema("target_vocabulary")["default"]["air_asset_kinds"]


def air_asset_kind(asset_id: Optional[str]) -> Optional[str]:
    """AIR 번호 → 종류(BLD·FAC·HOM·RET·PRT). 정본 정규식에 안 맞으면 None."""
    if matches("AirAssetId", asset_id) or matches("AirPortfolioId", asset_id):
        return asset_id.split("-")[1]
    return None
