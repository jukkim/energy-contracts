"""policy_measures.json + policy_evaluation_contract.Objective SSOT 가드 (0.3.8).

AgentLeague debate(F14 producer)의 inline POLICY_MEASURES/OBJECTIVES 를 SSOT 로 승격하며
신설. 본 테스트는 다음 불변식을 강제한다:
  1. MeasureCode enum == default.measures 키 집합 (코드↔메타 drift 가드)
  2. **코드 prefix 3+ 문자(ENV/PV/SRC/MAT)** — 단일문자 E?/S? 금지
     (legacy_ems_code_mapping.json#drift_guard 충돌 회피, 필수 제약 #3)
  3. metric ∈ MeasureMetric enum, base ∈ [0,1], eplus_ref = list[str]
  4. MeasureCode 네임스페이스가 ems_strategies StrategyCode(M00~M20)와 직교(교집합 0)
  5. policy_evaluation_contract.json#$defs.Objective enum 5종 정합
"""
from __future__ import annotations

import re

from energy_contracts import load_schema

_ALLOWED_PREFIXES = ("ENV", "PV", "SRC", "MAT")
_CODE_RE = re.compile(r"^(ENV|PV|SRC|MAT)\d{2}$")
# legacy_ems_code_mapping.json#drift_guard 가 deprecated 로 차단하는 단일문자 패턴
_FORBIDDEN_LEGACY_RE = re.compile(r"^[ES]\d{1,2}$")


def test_measure_codes_match_default_keys() -> None:
    pm = load_schema("policy_measures")
    enum_codes = pm["$defs"]["MeasureCode"]["enum"]
    default_keys = list(pm["default"]["measures"].keys())
    assert enum_codes == default_keys, (enum_codes, default_keys)
    assert len(enum_codes) == 8


def test_measure_code_prefix_3plus_chars() -> None:
    """필수 제약 #3 — prefix 3+ 문자, 단일문자 E?/S? 절대 금지."""
    pm = load_schema("policy_measures")
    for code in pm["$defs"]["MeasureCode"]["enum"]:
        assert _CODE_RE.match(code), f"{code} prefix 규약(ENV/PV/SRC/MAT + 2자리) 위반"
        assert code.startswith(_ALLOWED_PREFIXES), code
        assert not _FORBIDDEN_LEGACY_RE.match(code), (
            f"{code} 가 deprecated 단일문자 E?/S? 패턴과 충돌 — drift_guard 차단 대상")


def test_measure_meta_well_formed() -> None:
    pm = load_schema("policy_measures")
    metrics = set(pm["$defs"]["MeasureMetric"]["enum"])
    assert metrics == {
        "operational_kwh", "self_sufficiency", "primary_energy", "embodied_carbon"}
    for code, meta in pm["default"]["measures"].items():
        assert meta["metric"] in metrics, (code, meta["metric"])
        assert 0.0 <= meta["base"] <= 1.0, (code, meta["base"])
        assert isinstance(meta["eplus_ref"], list)
        assert all(isinstance(x, str) for x in meta["eplus_ref"])
        assert isinstance(meta["name"], str) and meta["name"]


def test_measure_namespace_orthogonal_to_strategy_code() -> None:
    """MeasureCode(자본·설계)와 StrategyCode(운영 EMS M00~M20) 직교 — 교집합 0."""
    pm = load_schema("policy_measures")
    ems = load_schema("ems_strategies")
    measure_codes = set(pm["$defs"]["MeasureCode"]["enum"])
    strategy_codes = set(ems["$defs"]["StrategyCode"]["enum"])
    assert measure_codes.isdisjoint(strategy_codes), (
        measure_codes & strategy_codes)


def test_objective_enum_registered() -> None:
    pe = load_schema("policy_evaluation_contract")
    obj = pe["$defs"]["Objective"]["enum"]
    assert obj == [
        "carbon_tco2", "primary_energy", "roi_payback",
        "equity_weighted", "peak_shift", "thermal_comfort"], obj
