"""NDC 감축목표·탄소가격 범위·DR 가정값 정본(2026-09-28) — 값 대조 + 반례.

반례 두 방향:
  * 막아야 할 것 — 건물부문 맥락이 국가 전체 40% 를 쓰는 것(기본 목표가 national 이면 실패).
  * 막으면 안 될 것 — 국가 전체 맥락의 40% 는 그대로 남아 있어야 한다(없어지면 실패).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from energy_contracts import load_schema

ROOT = Path(__file__).resolve().parents[1]


def _ndc() -> dict:
    return load_schema("energy_constants")["default"]["ndc_targets"]


def test_building_2030_rate_matches_published_emissions():
    t = _ndc()["targets"]["building_2030"]
    derived = 1 - t["target_emissions_mtco2eq"] / t["base_emissions_mtco2eq"]
    assert round(derived, 3) == t["reduction_rate"] == 0.328


def test_default_target_is_building_sector_not_national():
    ndc = _ndc()
    default = ndc["targets"][ndc["default_target"]]
    assert default["scope"] == "building"
    assert default["reduction_rate"] != ndc["targets"]["national_2030"]["reduction_rate"]


def test_national_40pct_kept_for_national_context():
    nat = _ndc()["targets"]["national_2030"]
    assert nat["scope"] == "national" and nat["reduction_rate"] == 0.40


def test_2035_building_is_range_without_single_rate():
    t = _ndc()["targets"]["building_2035"]
    assert "reduction_rate" not in t
    assert (t["reduction_rate_min"], t["reduction_rate_max"]) == (0.536, 0.562)


@pytest.mark.parametrize("key", ["national_2030", "building_2030", "building_2035"])
def test_every_target_carries_source(key):
    t = _ndc()["targets"][key]
    assert t["data_source"] == "external"
    assert t["source_url"].startswith("https://") and t["source_date"]


def test_every_target_validates_against_its_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = load_schema("energy_constants")
    jsonschema.validate(schema["default"], schema)
    bad = {**schema["default"], "ndc_targets": {"default_target": "x", "targets": {"y": {"scope": "city"}}}}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def _generated() -> dict:
    spec = importlib.util.spec_from_file_location("gc", ROOT / "scripts" / "gen_constants.py")
    gc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gc)  # type: ignore[union-attr]
    ns: dict = {}
    exec(gc.gen_python(gc.load_schemas()), ns)  # noqa: S102 — 생성본을 실제로 실행해 센다
    return ns


def test_generated_constants_carry_new_values_as_same_data():
    ns = _generated()
    assert ns["NDC_TARGETS"] == _ndc()
    assert ns["DR_ASSUMPTIONS"] == load_schema("ems_strategies")["default"]["dr_assumptions"]
    kau = ns["MARKET_PRICES"]["kau"]
    assert kau["fallback_krw_per_tco2"] == 20000
    assert (kau["phase4_2030_outlook_krw_per_tco2"]["min"],
            kau["phase4_2030_outlook_krw_per_tco2"]["max"]) == (40000, 61000)


def test_carbon_outlook_does_not_replace_default():
    kau = load_schema("market_prices")["default"]["kau"]
    rng = kau["phase4_2030_outlook_krw_per_tco2"]
    assert kau["fallback_krw_per_tco2"] < rng["min"] <= rng["max"]
    assert rng["source_urls"] and rng["as_of"]


# ── DR 가정값 ──────────────────────────────────────────────────────────────

def _dr() -> dict:
    return load_schema("ems_strategies")["default"]["dr_assumptions"]


def test_dr_block_validates_and_rejects_bad_code():
    jsonschema = pytest.importorskip("jsonschema")
    schema = load_schema("ems_strategies")
    jsonschema.validate(schema["default"], schema)
    bad_dr = {**_dr(), "strategies": {**_dr()["strategies"], "M05": {"formula_id": "x", "formula": "x",
                                                                     "controlled_load": "hvac", "source": "x"}}}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**schema["default"], "dr_assumptions": bad_dr}, schema)


def test_dr_covers_exactly_m16_to_m20_and_is_assumption_grade():
    dr = _dr()
    assert sorted(dr["strategies"]) == ["M16", "M17", "M18", "M19", "M20"]
    assert dr["evidence_grade"] == "assumption" and dr["data_source"] == "imputed" and dr["method"]
    classes = load_schema("data_classification")["$defs"]
    assert dr["data_source"] in classes["DataSource"]["enum"]
    assert dr["display_class"] in classes["EvidenceDisplayClass"]["enum"]


def test_m16_has_one_canonical_formula_and_named_variants():
    m16 = _dr()["strategies"]["M16"]
    assert m16["formula_id"] == "event_night_hvac_shed"
    assert "DR 이벤트" in m16["formula"] and "야간" in m16["formula"]
    ids = [v["id"] for v in m16["variants"]]
    assert ids == ["annual_setback_deepening", "nightly_hvac_shed"]
    assert all(v["status"] == "variant" for v in m16["variants"])
    assert m16["formula_id"] not in ids


def test_m19_hvac_proxy_is_missing_not_invented():
    m19 = _dr()["strategies"]["M19"]
    assert m19["hvac_proxy_depth"] is None
    absences = load_schema("data_classification")["$defs"]["AbsenceKind"]["enum"]
    assert m19["hvac_proxy_depth_absence"] == "missing" and "missing" in absences


def test_event_window_default_is_17_to_20_weekday_summer():
    w = _dr()["event_window_default"]
    assert (w["start"], w["end"], w["weekdays_only"], w["months"]) == ("17:00", "20:00", True, [7, 8])
    assert w["source_url"].startswith("https://")
