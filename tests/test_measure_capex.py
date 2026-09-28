"""전략별 가정 설치비(energy_contracts.measure_capex) — 식·정본 연결·반례."""
from __future__ import annotations

import pytest

from energy_contracts import load_schema, measure_capex
from energy_contracts.measure_capex import StrategyCapexUnavailable, all_strategy_capex, strategy_capex


def _block() -> dict:
    return load_schema("measure_cost_catalog")["default"]["ems_strategy_capex_assumption"]


def test_every_canonical_strategy_is_priced():
    codes = list(load_schema("ems_strategies")["default"]["strategies"])
    out = all_strategy_capex()
    assert list(out) == codes and len(out) == 23


def test_formula_uses_bems_unit_price_and_point_share():
    bems = load_schema("measure_cost_catalog")["default"]["measures"]["BEMS"]["capex_krw_per_m2"]
    n = len(_block()["point_universe"])
    r = strategy_capex("M04")
    assert r["control_points"] == ["hvac_setpoint"]
    assert r["capex_krw_per_m2"] == bems * 1 / n
    assert strategy_capex("M00")["capex_krw_per_m2"] == 0


def test_m04_and_m05_share_hardware_so_d10_compares_savings():
    assert strategy_capex("M04")["capex_krw_per_m2"] == strategy_capex("M05")["capex_krw_per_m2"]


def test_combined_is_union_of_components_not_hand_list():
    comps = load_schema("ems_strategies")["default"]["strategies"]["M11"]["components"]
    union = sorted({p for c in comps for p in strategy_capex(c)["control_points"]})
    assert strategy_capex("M11")["control_points"] == union
    assert "M11" not in _block()["single_strategy_points"]


def test_hardware_excluded_is_reported_for_ess_strategies():
    assert "M18" in strategy_capex("M18")["hardware_excluded"]
    assert "M18" in strategy_capex("M19")["hardware_excluded"]
    assert strategy_capex("M04")["hardware_excluded"] == {}


def test_result_is_labelled_assumption():
    r = strategy_capex("M17")
    assert (r["evidence_grade"], r["data_source"], r["source"]) == ("assumption", "imputed", "가정")


def test_unknown_code_is_named_refusal():
    with pytest.raises(StrategyCapexUnavailable):
        strategy_capex("M99")


def test_point_outside_universe_is_refused(monkeypatch):
    real = measure_capex._sources

    def patched():
        catalog, strategies = real()
        block = dict(catalog["ems_strategy_capex_assumption"])
        block["single_strategy_points"] = {**block["single_strategy_points"], "M04": ["no_such_point"]}
        return {**catalog, "ems_strategy_capex_assumption": block}, strategies

    monkeypatch.setattr(measure_capex, "_sources", patched)
    with pytest.raises(StrategyCapexUnavailable):
        strategy_capex("M04")


def test_capex_block_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = load_schema("measure_cost_catalog")
    jsonschema.validate(schema["default"], schema)
