"""telemetry.json v1.1 zones[] 필드 검증 — 하위 호환 + 존별 세부값.

- 레거시(zones 없음) payload 는 여전히 유효(forward-compat).
- zones[] 방출 payload 는 JSON Schema + pydantic 모델 양쪽 통과.
- zone item 은 zone_id 필수, 나머지 선택.
"""
from __future__ import annotations

import jsonschema
import pytest

from energy_contracts import load_schema
from energy_contracts._pydantic_models.telemetry import Telemetry


SCHEMA = load_schema("telemetry")


def _base() -> dict:
    return {"ven_id": "VEN-001", "timestamp": "2026-07-20T13:00:00+00:00", "power_kw": 12.4}


def test_legacy_payload_without_zones_valid():
    """zones 미포함 = 기존 장치 — 여전히 유효(하위 호환)."""
    payload = _base()
    jsonschema.validate(payload, SCHEMA)
    assert Telemetry.model_validate(payload).zones is None


def test_payload_with_zones_valid():
    payload = _base() | {
        "zones": [
            {"zone_id": "3F-S", "indoor_temp_c": 27.9, "hvac_setpoint_c": 24.0, "co2_ppm": 1250, "occupancy": True, "power_kw": 4.8},
            {"zone_id": "3F-N", "indoor_temp_c": 24.2, "humidity_pct": 46.0},
        ]
    }
    jsonschema.validate(payload, SCHEMA)
    model = Telemetry.model_validate(payload)
    assert model.zones is not None and len(model.zones) == 2
    assert model.zones[0].zone_id == "3F-S"
    assert model.zones[0].co2_ppm == 1250
    assert model.zones[1].hvac_setpoint_c is None  # 선택 필드 생략 허용


def test_zone_requires_zone_id():
    payload = _base() | {"zones": [{"indoor_temp_c": 24.0}]}  # zone_id 누락
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, SCHEMA)


def test_zone_co2_and_humidity_bounds():
    # humidity_pct 상한 100 초과 → 스키마 위반.
    payload = _base() | {"zones": [{"zone_id": "z1", "humidity_pct": 140}]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, SCHEMA)
