"""건물별 **점 설정**(`provision.OperatingConfig.point_settings`) 계약 게이트.

**왜 이 계약이 생겼나**: 건물마다 내릴 수 있는 축이 `objective` 하나뿐이었다.
실제 관제는 설정온도·조명·스케줄처럼 점 단위 값을 건물마다 다르게 준다. 엣지엔
점 제어 계층이 이미 있는데(`onsite/`: DeviceCatalog·Scope·Executor·value_spec)
**원격에서 들어갈 계약이 없었다** — 그래서 MGCC 는 `setpoint_c` 같은 키를 지어
보냈고, `additionalProperties` 가 열려 있어 검증을 통과한 뒤 아무도 읽지 않았다
(mgcc CLAUDE.md §5.9 "되는 것과 안 되는 것").

이 파일이 고정하는 것:
  ① 세 축(대상·성질·값)의 조합 규칙이 실제로 강제되는가
  ② guarded mirror 가 원본과 갈라지지 않았는가
"""
from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest

SCHEMAS = pathlib.Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator():
    return jsonschema.Draft202012Validator(_load("provision"))


def _payload(point_settings) -> dict:
    return {
        "provisioning_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "ven_id": "VEN-EP-WALL-00",
        "revision": 1,
        "issued_at": "2026-08-01T21:00:00+09:00",
        "authority": "mgcc",
        "config_merge": True,
        "config": {"ven_id": "VEN-EP-WALL-00",
                   "operating": {"point_settings": point_settings}},
    }


# --- 통과해야 하는 것 --------------------------------------------------------

ACCEPTED = {
    "단일값 물리점": [{"point_id": "KR.SITE-A.B1.hvac.AHU-1.SAT_SP",
                  "kind": "physical", "value": 22.0, "unit": "°C"}],
    "selector 다중 대상": [{"selector": {"equipment_kind": "lighting", "floor": 3},
                       "kind": "physical", "value": 70}],
    "값 여러개(존별)": [{"kind": "virtual",
                    "values": [{"zone": "Z-1", "value": 23.0},
                               {"zone": "Z-2", "value": 25.0}]}],
    "스케줄(자정 넘김 포함)": [{"point_id": "KR.S.B.hvac.AHU-1.ZN_T_SP", "kind": "schedule",
                       "schedule": [
                           {"days": ["mon", "tue", "wed", "thu", "fri"],
                            "start": "08:00", "end": "18:00", "value": 22.0},
                           {"start": "22:00", "end": "06:00", "value": 27.0}],
                       "fallback": 25.0}],
    "cmd 역할 + 우선순위": [{"point_id": "KR.S.B.lighting.L-3F.CMD", "kind": "physical",
                       "role": "cmd", "value": True, "priority": 8}],
    "빈 배열 = 전부 해제": [],
}


@pytest.mark.parametrize("name", sorted(ACCEPTED))
def test_valid_point_settings_pass(validator, name):
    errs = list(validator.iter_errors(_payload(ACCEPTED[name])))
    assert not errs, f"{name}: {[e.message for e in errs][:2]}"


# --- 거부해야 하는 것 --------------------------------------------------------

REJECTED = {
    # 대상 축 — 무엇을 바꾸라는 건지 알 수 없거나, 어느 쪽이 이기는지 갈린다
    "대상 없음": [{"kind": "physical", "value": 22.0}],
    "대상 둘(point_id+selector)": [{"point_id": "a", "selector": {"floor": 1},
                                "kind": "physical", "value": 1}],
    "selector 빈 객체": [{"selector": {}, "kind": "physical", "value": 1}],
    # 값 축 — 정확히 하나여야 한다
    "값 둘(value+schedule)": [{"point_id": "a", "kind": "physical", "value": 1,
                            "schedule": [{"start": "08:00", "end": "09:00", "value": 2}]}],
    "값 없음": [{"point_id": "a", "kind": "physical"}],
    # 성질 축 — 종류만 스케줄이라 해 놓고 단일값을 보내면 무엇을 기대한 건지 모른다
    "kind=schedule 인데 단일값": [{"point_id": "a", "kind": "schedule", "value": 22}],
    "미지의 kind": [{"point_id": "a", "kind": "analog", "value": 1}],
    # 형식 — 조용히 어긋나면 밤중에 설비가 제멋대로 움직인다
    "시각 형식(8:00)": [{"point_id": "a", "kind": "schedule",
                     "schedule": [{"start": "8:00", "end": "18:00", "value": 1}]}],
    "요일 어휘(monday)": [{"point_id": "a", "kind": "schedule",
                       "schedule": [{"days": ["monday"], "start": "08:00",
                                     "end": "09:00", "value": 1}]}],
    "priority 범위 밖": [{"point_id": "a", "kind": "physical", "value": 1, "priority": 0}],
    "미지의 필드": [{"point_id": "a", "kind": "physical", "value": 1, "oops": 1}],
}


@pytest.mark.parametrize("name", sorted(REJECTED))
def test_invalid_point_settings_are_rejected(validator, name):
    assert list(validator.iter_errors(_payload(REJECTED[name]))), \
        f"{name}: 통과했다 — 계약이 이 조합을 막지 못한다"


# --- guarded mirror 가드 ------------------------------------------------------

def test_mirrored_vocabularies_match_their_source():
    """복제한 값집합이 원본과 갈라지지 않았는가.

    교차 파일 `$ref` 는 일반 검증기가 못 푼다(실측: `Unresolvable:
    telemetry.json#/$defs/PointKind`). 그래서 복제하되, 손으로 갈라지면 여기서
    먼저 깨진다 — **읽을 때와 쓸 때 같은 점을 다른 이름으로 부르면** 소비단마다
    뜻이 갈린다.
    """
    ps = _load("provision")["$defs"]["PointSetting"]["properties"]
    tel, eq = _load("telemetry"), _load("equipment_taxonomy")
    pairs = [
        ("kind", ps["kind"]["enum"], tel["$defs"]["PointKind"]["enum"]),
        ("role", ps["role"]["enum"], eq["$defs"]["PointRole"]["enum"]),
        ("selector.equipment_kind", ps["selector"]["properties"]["equipment_kind"]["enum"],
         eq["$defs"]["EquipmentKind"]["enum"]),
    ]
    for label, mirror, source in pairs:
        assert mirror == source, f"{label} 이 원본과 갈라졌다: {mirror} != {source}"


def test_point_mnemonic_shares_the_address_vocabulary():
    """selector 의 점 이름은 CPA `{point}` 세그먼트와 **같은 어휘**여야 한다.

    표준 니모닉을 그대로 들여오지 않으면 같은 급기온도를 SAT/DAT 로 다르게 부르게
    된다(equipment_taxonomy `EquipmentPoint.mnemonic` 주석과 같은 이유).
    """
    prov = _load("provision")["$defs"]["PointSetting"]
    eq = _load("equipment_taxonomy")
    assert (prov["properties"]["selector"]["properties"]["point_mnemonic"]["pattern"]
            == eq["$defs"]["EquipmentPoint"]["properties"]["mnemonic"]["pattern"])
