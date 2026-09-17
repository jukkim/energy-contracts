"""korean_building_standards.json ↔ 법령 원문 대조기 — 변이 시험 (2026-09-17).

정본 값을 한 칸씩 틀리게 바꿔 대조기가 **그 칸을** 잡는지 본다. 통과만 보는 시험은 대조기가 아무것도 안 봐도 초록이다.
"""
from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("_vkls", ROOT / "scripts" / "verify_korean_law_sources.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

pytest.importorskip("pypdf")
TODAY = dt.date(2026, 9, 17)
BASE = json.loads(V.SCHEMA.read_text(encoding="utf-8"))
SIM = json.loads(V.SIM_SCN.read_text(encoding="utf-8"))


def _run(tmp_path, monkeypatch, mutate=None, mutate_sim=None):
    d, s = copy.deepcopy(BASE), copy.deepcopy(SIM)
    if mutate:
        mutate(d["default"])
    if mutate_sim:
        mutate_sim(s["default"])
    a, b = tmp_path / "kbs.json", tmp_path / "sim.json"
    a.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    b.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(V, "SCHEMA", a)
    monkeypatch.setattr(V, "SIM_SCN", b)
    return V.verify(TODAY)


def test_committed_schema_matches_originals(tmp_path, monkeypatch):
    rc, msgs = _run(tmp_path, monkeypatch)
    assert rc in (0, 2), msgs            # 2 = pyhwp 없음(프로필만 못 잼) — 실패로 세지 않되 통과로도 세지 않는다
    if rc == 2:
        assert all("HWP" in m for m in msgs), msgs


def _set(path, value):
    def f(d):
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


@pytest.mark.parametrize("path,value,expect", [
    (("envelope_u_limits", "window", "direct", "other", "중부1"), 1.2, "envelope_u_limits"),         # 옛 코드 값
    (("envelope_u_limits", "window", "direct", "apartment", "중부1"), 1.0, "envelope_u_limits"),     # 옛 코드 값
    (("envelope_u_limits", "floor", "direct", "no_floor_heating", "제주"), 0.35, "envelope_u_limits"),
    (("envelope_u_limits", "door", "direct", "other", "남부"), 2.2, "병합 셀"),                        # 창·문 병합 깨짐
    (("envelope_u_limits", "roof", "direct", "중부2"), 0.17, "병합 셀"),
    (("ventilation", "multi_use_per_person_m3h", "medical"), 29, "medical"),
    (("ventilation", "school", "per_person_m3h"), 25.0, "ventilation.school"),
    (("assessment_conditions", "zeb_setpoints", "cooling_c"), 24, "zeb_setpoints"),
    (("design_indoor_conditions", "rows", "office", "heating_c"), [20, 22], "office"),
    (("climate_zones", "definitions", "중부2"), "부산광역시, 서울특별시", "중부2"),
    (("surface_resistances", "wall", "outside_direct"), 0.04, "surface_resistances"),       # ISO 6946 값(원문 아님)
    (("surface_resistances", "lowest_floor", "outside_indirect"), 0.17, "surface_resistances"),
    (("air_layer_resistances", "site_built", "above"), 0.17, "air_layer_resistances"),
    (("envelope_surface_rules", "indirect"), "외기가 직접 통하지 아니하는 비난방 공간에 접한 부위", "envelope_surface_rules.indirect"),
])
def test_each_mutation_is_caught(tmp_path, monkeypatch, path, value, expect):
    rc, msgs = _run(tmp_path, monkeypatch, _set(path, value))
    assert rc == 1 and any(expect in m for m in msgs), msgs


def test_sha_mismatch_is_caught(tmp_path, monkeypatch):
    rc, msgs = _run(tmp_path, monkeypatch, _set(("sources", "esdc_2026_360", "annexes", "1", "sha256"), "0" * 64))
    assert rc == 1 and any("sha256" in m for m in msgs)


def test_missing_original_is_unmeasured_not_pass(tmp_path, monkeypatch):
    rc, msgs = _run(tmp_path, monkeypatch,
                    _set(("sources", "zeb_criteria_2024_893", "annexes", "3", "file"), "docs/legal_sources/none.pdf"))
    assert rc != 0


def test_derived_copy_drift_is_caught(tmp_path, monkeypatch):
    rc, msgs = _run(tmp_path, monkeypatch, mutate_sim=_set(("ko_envelope_uvalue", "central_2", "roof"), 0.17))
    assert rc == 1 and any("ko_envelope_uvalue" in m for m in msgs)


def test_currency_expiry(tmp_path, monkeypatch):
    d = copy.deepcopy(BASE)
    a = tmp_path / "kbs.json"
    a.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(V, "SCHEMA", a)
    rc, msgs = V.verify(dt.date(2027, 1, 1))
    assert rc in (2, 3)
    if rc == 3:
        assert "기한" in msgs[0]


def test_profile_mutation_is_caught_when_hwp_readable(tmp_path, monkeypatch):
    rc0, _ = _run(tmp_path, monkeypatch)
    if rc0 == 2:
        pytest.skip("pyhwp 없음 — 프로필 대조 못 잼")
    rc, msgs = _run(tmp_path, monkeypatch, _set(("usage_profiles", "profiles", "office_large", "equipment_heat_wh_per_m2d"), 42.0))
    assert rc == 1 and any("equipment_heat" in m for m in msgs), msgs
    rc, msgs = _run(tmp_path, monkeypatch, _set(("usage_profiles", "profiles", "retail", "monthly_use_days"), [26] * 12))
    assert rc == 1 and any("monthly_use_days" in m for m in msgs), msgs
