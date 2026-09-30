# -*- coding: utf-8 -*-
"""0.3.72 (2026-09-30) — 일반화 단계 소비처가 기다리는 행(요청 C1~C11 · WP6 R10, 캠페인 scratch/wp_requests/EC_ROWS_NEEDED.md).

게이트웨이 코드는 이 행들이 없으면 되묻거나(겨울·봄·가을) · 그리지 않거나(층 없는 훑기) · 거절한다. 그래서 여기서 본다:
① 새 행의 모양과 **요청 값 그대로**(moved_literal = 오늘 코드 값) ② 0.3.71 태그와 **잎 전부** 대조(문구 포함 — 예외는 사용자 결정 둘)
③ 어휘 적재 검사(한 별칭 = 한 열쇠 · 가리키는 열쇠 존재) — 통과 쪽과 막아야 할 쪽 양쪽 ④ 질문 계절 체계가 계절 넷을 푼다
⑤ 새 행이 생성본에 닿는다(생성기는 표를 통째로 파생) ⑥ 넣지 않기로 한 요청이 행으로 새지 않았다. 검사가 돈 건수를 단언한다.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))

import gen_constants as gc  # noqa: E402
import validate_ssot as vs  # noqa: E402
import vocabulary_gate as vg  # noqa: E402

# 행 모양 규칙은 0.3.70 시험의 한 함수(두 벌을 두지 않는다)
_spec = importlib.util.spec_from_file_location("_t0370", Path(__file__).with_name("test_declared_assumptions_0370.py"))
_t0370 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t0370)
row_problems = _t0370.row_problems

NEW_ROWS_0372 = (
    "demo_user_answers",                                                                             # C11
    "economics_horizon_years_default", "financial_candidate_measures_max", "climate_load_shift",     # C9
    "facility_use_classes", "small_building_area_m2_default", "cohort_bands_default", "cohort_segmentation_default",  # C10
    "forecast_horizon_default", "period_substitution", "ranking_basis_default", "schedule_event_nouns",  # C5
    "drop_sustain_share_of_threshold",                                                               # C8
    "quadrant_split_default", "priority_axis_defaults",                                              # C4
    "debate_axis_scales", "debate_recalc_fixtures", "debate_numeric_rules", "debate_calendar", "debate_family_critics",  # C6
    "indoor_design_rh_pct",                                                                          # C3
    "diagnosis_risk_thresholds", "home_baseload_low_share", "appliance_exhaustive_search_max",
    "drop_reference_days_default", "drop_integrity_rule",                                            # C7
    "action_review", "virtual_action_effects", "lhs_axis", "virtual_start_shift", "sim_pack_analysis_defaults",
    "virtual_population_shares",                                                                     # C2
    "policy_adverse_boundary",                                                                       # WP6 R10
)
CHANGED_SCHEMAS = ("declared_assumptions.json", "calendar_conventions.json", "equipment_taxonomy.json", "measure_cost_catalog.json",
                   "ems_strategies.json", "data_classification.json", "target_vocabulary.json", "region_codes.json",
                   "error_response.json", "judgement_thresholds.json")
#: 0.3.71 에서 **바뀌어도 되는** 잎 — 판 표지와 사용자·EC 소유자 결정(계절 체계) 둘, retry 열거는 뒤에 붙이기만(아래에서 따로 본다)
ALLOWED_CHANGES = {"/version", "/updated", "/$comment",
                   "calendar_conventions.json:/default/question_season_system",
                   "calendar_conventions.json:/default/question_season_system_note",
                   "error_response.json:/$defs/Refusal/properties/retry/enum",
                   "error_response.json:/$defs/Refusal/properties/retry/description"}


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _declared() -> dict:
    return _load("declared_assumptions.json")["default"]


def _at_tag(tag: str, name: str) -> dict | None:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "show", f"{tag}:energy_contracts/schemas/{name}"],
                             capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return json.loads(out.stdout.decode("utf-8"))


# ── ① 새 행 ────────────────────────────────────────────────────────────────────────────────────────────────
def test_new_rows_exist_with_the_row_shape_and_no_invented_citation():
    d, units = _declared(), set(_load("interface_types.json")["$defs"]["QuantityUnit"]["enum"])
    missing = [k for k in NEW_ROWS_0372 if k not in d]
    assert not missing, missing
    problems = [p for k in NEW_ROWS_0372 for p in row_problems(k, d[k], units)]
    assert not problems, problems
    assert len(NEW_ROWS_0372) == len(set(NEW_ROWS_0372)) == 33
    # 외부 근거를 짓지 않았다 — 새 행에 표준 인용은 없다(인용이 있는 요청은 robust_z 하나이고 그것은 judgement_thresholds 에 있다)
    kinds = {k: d[k]["basis_kind"] for k in NEW_ROWS_0372}
    assert "standard_citation" not in kinds.values(), kinds
    demo = [k for k, v in kinds.items() if v == "declared_demo_assumption"]
    assert demo and all("선언" in d[k]["basis"] for k in demo), demo
    moved = [k for k, v in kinds.items() if v == "moved_literal"]
    assert len(moved) + len(demo) == 33 and len(moved) >= 25, (len(moved), len(demo))


#: 요청 표의 값 그대로(EC_ROWS_NEEDED — moved_literal 은 오늘 코드 값). 큰 표는 잎 몇 개를 따로 본다.
EXPECTED_VALUES = {
    "demo_user_answers": {"energy_budget_share_of_monthly_cost": 0.95, "maintenance_budget_share_of_annual_cost": 0.10,
                          "replacement_measure_code": "CHIL", "failure_probability_rule": "1/lifetime_yr",
                          "downtime_share_of_unit_replacement": 0.20, "action_result_word": "재발",
                          "event_reservation_rule": "shortest_span"},
    "economics_horizon_years_default": 10,
    "financial_candidate_measures_max": 4,
    "climate_load_shift": {"baseline": {}, "ssp245_2050": {"cooling_elec": 1.25, "heating_gas": 0.85},
                           "ssp585_2050": {"cooling_elec": 1.40, "heating_gas": 0.75},
                           "ssp585_2080": {"cooling_elec": 1.60, "heating_gas": 0.65}},
    "small_building_area_m2_default": 1000.0,
    "cohort_bands_default": {"area_edges_m2": [500, 1000, 3000, 5000, 10000], "era_edges": [1980, 1990, 2010],
                             "payback_band_edges_yr": [3, 5, 10, 15]},
    "cohort_segmentation_default": {"k": 4, "outlier_share": 0.01},
    "forecast_horizon_default": {"horizon_hours": 24, "step_hours": 1},
    "period_substitution": {"nearest_year_max_shift_yr": 6},
    "ranking_basis_default": "원단위(면적당 사용량)",
    "drop_sustain_share_of_threshold": 0.5,
    "quadrant_split_default": "median",
    "priority_axis_defaults": {"difficulty_score_neutral": 0.5},
    "debate_numeric_rules": {"comfort_band_c": [22, 26], "imputation_max_gap_h": 3, "utility_floor": 0.01, "utility_ceiling": 0.99,
                             "assumption_min_gain": 0.05, "assumption_shrink": 0.5, "half_factor": 0.5, "resolution_guard_minutes": 15},
    "debate_calendar": {"hours_per_year": 8760.0, "months_per_year": 12},
    "debate_family_critics": {"numeric": ["data", "economic", "carbon", "legal"], "shortage": ["data", "legal", "safety"],
                              "assumption": ["economic", "carbon", "legal", "data"], "redebate": ["data", "economic", "safety", "carbon"],
                              "audit": ["data", "legal"]},
    "indoor_design_rh_pct": 50.0,
    "diagnosis_risk_thresholds": {"night_excess_share_pct": 5.0, "month_increase_pct": 10.0, "peak_to_mean_ratio": 2.0,
                                  "imputed_hour_share_pct": 10.0},
    "home_baseload_low_share": 0.10,
    "appliance_exhaustive_search_max": 4,
    "drop_reference_days_default": 28,
    "drop_integrity_rule": {"drop_threshold_pct": 30.0, "min_interval_days": 3, "reference_full_days_min": 14, "daily_rows_min": 28},
    "virtual_action_effects": {"setpoint_up": {"cooling_cut": [0.08, 0.15]}, "night_hvac_off": {"restart_boost": [0.30, 0.60]},
                               "deadband_widen": {"cooling_cut": [0.06, 0.12], "cycle_hours": [22, 6], "cycle_on_factor": 1.6},
                               "early_lights_off": {"base_cut": [0.05, 0.10]},
                               "filter_replace": {"cooling_cut": [0.03, 0.08], "airflow_gain": [0.08, 0.18]},
                               "coil_clean": {"cooling_cut": [0.05, 0.12], "airflow_gain": [0.04, 0.10]}},
    "lhs_axis": {"default_delta_share": 0.1, "t_min": 2.0, "min_samples_over_params": 10, "occupancy_delta_share": 0.2},
    "virtual_start_shift": {"default_hours": 2, "temp_rise_c_per_h": 0.5, "search_last_hour": 14},
    "sim_pack_analysis_defaults": {"range_quantiles": [0.1, 0.9], "success_rate_band": {"low": 0.2, "high": 0.6}, "min_pairs": 10,
                                   "min_baseline_samples": 10},
    "virtual_population_shares": {"elderly_share_range": [0.10, 0.30]},
    "policy_adverse_boundary": 0,
}


def test_values_are_exactly_the_requested_values():
    d = _declared()
    checked = 0
    for key, value in EXPECTED_VALUES.items():
        assert d[key]["value"] == value, key
        checked += 1
    # 큰 표 — 요청이 적은 잎
    ar = d["action_review"]["value"]
    assert (ar["base_quantile"], ar["high_quantile"], ar["on_share"], ar["completeness_min"], ar["intervals_shown"],
            ar["channels_listed"]) == (0.10, 0.95, 0.20, 0.90, 40, 20); checked += 1
    assert ar["inspection_score_weights"] == {"fault": 3, "setting": 2, "unknown": 1}; checked += 1
    assert ar["windows"]["quarter_lessons_sop"] == {"span_days": 91, "pre_days": 28, "action_day_margin_days": 14}; checked += 1
    assert ar == {"base_quantile": 0.10, "high_quantile": 0.95, "on_share": 0.20, "recurring_days": 3, "stopped_share": 0.10,
                  "base_collapse_share": 0.5, "deviation_floor_share": 0.05, "typical_min_samples": 3, "low_service_share": 0.85,
                  "burden_increase_share": 0.10, "pilot_share": 0.20, "pilot_min_for_rollout": 3, "control_drift_share": 0.05,
                  "completeness_min": 0.90, "representative_ratio_band": [0.5, 2.0], "min_pre_days": 7, "min_measured_days_for_fill": 7,
                  "inspection_score_weights": {"fault": 3, "setting": 2, "unknown": 1}, "intervals_shown": 40, "members_listed": 40,
                  "channels_listed": 20,
                  "windows": {"pilot_rollout": {"span_days": 56, "pre_days": 28}, "side_effects": {"span_days": 56, "pre_days": 28},
                              "mv_scenes": {"span_days": 56, "pre_days": 28},
                              "quarter_lessons_sop": {"span_days": 91, "pre_days": 28, "action_day_margin_days": 14}},
                  "closing_hours": {"round_the_clock": [2, 3, 4], "tail_hours": 2}} and len(ar) == 23; checked += 1
    axis = d["debate_axis_scales"]["value"]
    assert len(axis) == 42 and axis["_unbound"] == 1 and axis["법규"] == 1 and axis["CAPEX"] == 1e8 and axis["요금"] == 1e7; checked += 1
    fx = d["debate_recalc_fixtures"]["value"]
    assert sorted(fx) == sorted(["comfort_limit", "budget_portfolio", "operating_hours", "sensor_coverage", "tariff_pareto", "tenant_veto",
                                 "sign_disagreement", "strategy_hypotheses", "robust_capacity", "staff_schedule"]); checked += 1
    assert fx["budget_portfolio"]["before"]["budget_KRW"] == 100 and fx["staff_schedule"]["after"] == {"staff_count": 1}; checked += 1
    fac = d["facility_use_classes"]["value"]["cooling_shelter_candidate"]
    assert (fac["uses"], fac["use_prefixes"], fac["classification"]) == (["14100"], ["11"], "estimated"); checked += 1
    assert "원문 대조 전" in fac["basis"] and fac["names_ko"] == ["무더위쉼터", "쉼터", "냉방 쉼터"]; checked += 1
    ev = d["schedule_event_nouns"]["value"]
    assert ev["nouns"] == ["특별 행사", "행사", "축제", "대관", "세미나", "공연", "박람회", "학회", "체육대회", "콘서트"]; checked += 1
    assert ev["nouns_needing_date_word"] == ["이벤트"] and ev["date_words"] == ["날짜", "일정", "기간", "당일", "날", "일", "때"]; checked += 1
    # 기존 행 값 안의 새 칸(값) · 전송 주기 이름
    assert d["hazard_week_scenarios"]["value"]["cold"] == [
        {"id": "optimistic", "offset_c": 0.0, "label_ko": "낙관(한파 문턱 수준이 이어짐)"},
        {"id": "mid", "offset_c": -2.0, "label_ko": "중간(문턱 − 2℃)"},
        {"id": "conservative", "offset_c": -4.0, "label_ko": "보수(문턱 − 4℃)"}]; checked += 1
    lim = d["serving_display_limits"]["value"]
    assert (lim["presentation_table_max_columns"], lim["presentation_chart_max_series"]) == (12, 6); checked += 1
    scene = d["scene_motion_defaults"]["value"]
    assert scene["descend_keys"] == [[600, -85], [300, -45], [150, -12]] and scene["dive_building_end_alt_m"] == 250; checked += 1
    sched = d["sim_schedule_inference"]["value"]
    assert (sched["morning_window_hours"], sched["startup_window_hours"]) == (12, 2); checked += 1
    by = d["comm_status_thresholds"]["by_delivery"]
    assert (by["hourly_realtime"]["label_ko"], by["daily_batch"]["label_ko"]) == ("시간 단위 실시간", "일 배치"); checked += 1
    # 다른 스키마
    assert _load("calendar_conventions.json")["default"]["question_season_system"] == "meteorological"; checked += 1
    measures = _load("measure_cost_catalog.json")["default"]["measures"]
    assert {k: m["aliases_ko"] for k, m in measures.items()} == {
        "LED": ["전등", "형광등", "조명등"], "CHIL": ["칠러", "터보 냉동기"], "WIN": ["창문", "유리창", "이중창", "삼중창"],
        "INS": ["단열재", "외단열", "내단열"], "SEAL": ["틈새", "침기"], "SHAD": ["블라인드", "어닝", "차양막"],
        "VSD": ["가변속", "인버터 펌프", "인버터 팬"], "ERV": ["전열교환기", "폐열회수"], "HP": ["열펌프"], "COND": ["콘덴싱"],
        "RCX": ["설비 재조정", "커미셔닝"], "BEMS": ["건물에너지관리시스템"]}; checked += 1
    eq = _load("equipment_taxonomy.json")["default"]
    assert eq["aliases_ko"] == {
        "hvac": ["공조 보조", "냉난방기", "에어컨"], "vrf": ["EHP", "GHP", "시스템 에어컨", "시스템에어컨"], "ahu": ["공조기", "공조"],
        "chiller": ["냉동기", "칠러", "냉동"], "boiler": ["보일러"], "fan": ["송풍기", "팬"], "pump": ["펌프"], "lighting": ["조명"],
        "plug": ["콘센트", "전산실", "주방", "급식실", "조리"], "refrigeration": ["냉장", "쇼케이스"], "dhw": ["급탕"],
        "cooling_tower": ["냉각탑"], "erv": ["전열교환기"], "other": ["승강기", "엘리베이터", "에스컬레이터"]}; checked += 1
    rz = _load("judgement_thresholds.json")["default"]["anomaly"]["robust_z"]
    assert (rz["value"], rz["comparison"], rz["statistic"], rz["mad_to_sigma"], rz["basis_kind"]) == \
        (3.5, "at_least", "modified_z_mad", 1.4826, "standard_citation") and "Iglewicz & Hoaglin (1993)" in rz["basis"]; checked += 1
    assert _load("error_response.json")["$defs"]["Refusal"]["properties"]["retry"]["enum"] == ["ask", "fill", "none", "later"]; checked += 1
    kinds = _load("target_vocabulary.json")["default"]["air_asset_kinds"]
    assert {k: v.get("aliases_ko") for k, v in kinds.items() if "aliases_ko" in v} == \
        {"HOM": ["집"], "RET": ["매장", "가게", "지점"], "BLD": ["사옥", "빌딩"]}; checked += 1
    assert _load("data_classification.json")["default"]["classification"]["words"]["estimated"]["aliases_ko"] == ["근사", "범위"]; checked += 1
    sig = {c: m.get("observable_signature") for c, m in _load("ems_strategies.json")["default"]["strategies"].items()
           if m.get("observable_signature")}
    assert {c: (s["metric"], s["op"], s["threshold"], s.get("high")) for c, s in sig.items()} == {
        "M00": ("night_to_day_ratio", "lt", 0.5, None), "M01": ("weekday_ramp_hour", "within", [5, 8], None),
        "M10": ("peak_plateau_day_share", "ge", 0.5, 0.7), "M16": ("weekend_to_weekday_ratio", "lt", 0.6, None)}; checked += 1
    assert sig["M00"]["params"] == {"night_hours": [0, 6], "day_hours": [9, 18]} and \
        sig["M10"]["params"] == {"top_hours": 3, "plateau_share_of_day_max": 0.97} and sig["M01"]["params"] == {"ramp_share": 0.5}; checked += 1
    cities = _load("region_codes.json")["default"]["simulation_cities"]
    assert {c["name_en"] for c in cities.values() if c["coastal"]} == \
        {"Busan", "Incheon", "Ulsan", "Gangneung", "Jeju", "Pohang", "Changwon", "Mokpo"}; checked += 1
    assert all(isinstance(c["coastal"], bool) and c["coastal_basis"] for c in cities.values()) and len(cities) == 18; checked += 1
    assert checked == len(EXPECTED_VALUES) + 27, checked       # 28 행 값 + 잎·다른 스키마 27


# ── ② 0.3.71 태그와 잎 전부(문구 포함) ─────────────────────────────────────────────────────────────────────────
def strict_additive(old, new, path: str, allowed: set[str], file: str) -> tuple[list[str], int]:
    """old 의 모든 잎이 new 에 **같은 값**으로 있는가(문구도 — 새 키는 된다). 바뀌어도 되는 자리는 allowed(파일:경로 또는 경로)."""
    if path in allowed or f"{file}:{path}" in allowed:
        return [], 0
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [f"{file}:{path}: dict 가 아니게 됐다"], 0
        out, n = [], 0
        for key, value in old.items():
            if key not in new:
                out.append(f"{file}:{path}/{key}: 키가 사라졌다")
                continue
            sub, k = strict_additive(value, new[key], f"{path}/{key}", allowed, file)
            out += sub
            n += k
        return out, n
    if isinstance(old, list) and any(isinstance(v, (dict, list)) for v in old):
        if not isinstance(new, list) or len(new) != len(old):
            return [f"{file}:{path}: 목록 길이가 바뀌었다"], 0
        out, n = [], 0
        for i, (a, b) in enumerate(zip(old, new)):
            sub, k = strict_additive(a, b, f"{path}[{i}]", allowed, file)
            out += sub
            n += k
        return out, n
    return ([] if old == new and type(old) is type(new) else [f"{file}:{path}: {old!r} -> {new!r}"]), 1


def test_additive_against_the_0371_tag():
    """0.3.71 을 import 하는 코드가 그대로 돈다 — 열 파일의 문서 전체(스키마 칸 · 값 · 문구)를 태그와 잎마다 맞댄다."""
    checked = 0
    for name in CHANGED_SCHEMAS:
        old = _at_tag("v0.3.71", name)
        if old is None:
            pytest.skip(f"[해당 없음] git 태그 v0.3.71 을 못 읽었다({name}) — 통과가 아니다(못 잼)")
        problems, n = strict_additive(old, _load(name), "", ALLOWED_CHANGES, name)
        assert not problems, problems
        checked += n
    # 바뀌어도 되는 자리도 모양은 지킨다: retry 열거는 뒤에 붙이기만 · 계절 체계는 정한 값
    old_enum = _at_tag("v0.3.71", "error_response.json")["$defs"]["Refusal"]["properties"]["retry"]["enum"]
    new_enum = _load("error_response.json")["$defs"]["Refusal"]["properties"]["retry"]["enum"]
    assert new_enum[:len(old_enum)] == old_enum and new_enum[len(old_enum):] == ["later"]
    assert _at_tag("v0.3.71", "calendar_conventions.json")["default"]["question_season_system"] is None
    assert checked > 3000, checked                      # 열 파일의 잎 전부(실측 3,212 — 0 건이면 그것이 사고다)


def test_strict_additive_blocks_what_it_must():
    old = {"a": {"value": {"x": 1}, "rule_ko": "옛 문장"}, "rows": [{"c": 1}], "q": None}
    same = copy.deepcopy(old)
    same["a"]["value"]["y"] = 2                           # 새 칸은 된다
    same["b"] = {"value": 3}                              # 새 행은 된다
    same["q"] = "meteorological"                          # 허락한 자리는 된다
    assert strict_additive(old, same, "", {"/q"}, "f") == ([], 3)
    blocked = 0
    for mutate, allowed in ((lambda d: d["a"].update(rule_ko="새 문장"), {"/q"}),       # 0.3.71 시험과 달리 문구도 막는다
                            (lambda d: d["a"]["value"].update(x=1.0), {"/q"}),          # 1 → 1.0 도 바뀐 것(형)
                            (lambda d: d["a"]["value"].pop("x"), {"/q"}),
                            (lambda d: d["rows"].append({"c": 2}), {"/q"}),
                            (lambda d: d["rows"][0].update(c=5), {"/q"}),
                            (lambda d: d.update(q="kepco_tariff"), set())):             # 허락하지 않은 자리의 결정 값
        bad = copy.deepcopy(old)
        mutate(bad)
        assert strict_additive(old, bad, "", allowed, "f")[0], mutate
        blocked += 1
    assert blocked == 6


def test_no_new_schema_validation_errors_against_the_tag():
    """새 칸이 스키마를 어기지 않는다 — 기본값 검증 오류 목록이 태그와 같다(equipment_taxonomy 의 옛 오류 3건은 그대로 · 새 오류 0)."""
    checked = 0
    for name in CHANGED_SCHEMAS:
        new = _load(name)
        old = _at_tag("v0.3.71", name)
        if old is None:
            pytest.skip("[해당 없음] 태그를 못 읽었다 — 못 잼")
        errs = lambda s: sorted((list(e.path), e.message) for e in Draft202012Validator(s).iter_errors(s.get("default", {})))  # noqa: E731
        assert [e for e in errs(new) if e not in errs(old)] == [], name
        checked += 1
    assert checked == len(CHANGED_SCHEMAS)
    # 막아야 할 것: 새 어휘 칸의 스키마가 실제로 거른다(빈 말 · 겹친 말 · 없는 종류 · 없는 분류)
    et = _load("equipment_taxonomy.json")
    sub = lambda prop: Draft202012Validator({"$defs": et["$defs"], **et["properties"][prop]})  # noqa: E731
    assert not list(sub("aliases_ko").iter_errors(et["default"]["aliases_ko"]))
    assert not list(sub("labels_ko").iter_errors(et["default"]["labels_ko"]))
    assert not list(sub("dr_class").iter_errors(et["default"]["dr_class"]))
    for prop, bad in (("aliases_ko", {"hvac": ["에어컨", "에어컨"]}), ("aliases_ko", {"hvac": [""]}), ("aliases_ko", {"heat_pump": ["x"]}),
                      ("labels_ko", {"hvac": {"name_ko": "x"}}), ("dr_class", {"classes": {}, "by_kind": {"lighting": "shed"}})):
        assert list(sub(prop).iter_errors(bad)), (prop, bad)
    mc = _load("measure_cost_catalog.json")
    bad = copy.deepcopy(mc["default"])
    bad["measures"]["LED"]["aliases_ko"] = ["전등", "전등"]
    assert list(Draft202012Validator(mc).iter_errors(bad))


# ── ③ 어휘 적재 검사 — 통과 쪽 · 막는 쪽 ────────────────────────────────────────────────────────────────────
def test_vocabulary_gate_passes_and_finds_every_vocabulary():
    docs = vg._load_dir(SCHEMAS)
    problems, checks = vg.problems(docs)
    assert problems == [] and checks >= 300, (problems, checks)
    found = {(name, where) for name, doc in docs.items() for where, _ in vg.discover(doc.get("default"), "")}
    # 손 목록 없이 찾은 어휘 — 여섯 곳이 다 잡혀야 한다(하나라도 빠지면 그 어휘는 검사 밖이다)
    assert {("measure_cost_catalog", "/measures"), ("equipment_taxonomy", "/aliases_ko"), ("equipment_taxonomy", "/labels_ko"),
            ("target_vocabulary", "/air_asset_kinds"), ("data_classification", "/classification/words"),
            ("declared_assumptions", "/facility_use_classes/value")} <= found, found


def _mutations():
    """(이름, 문서 고치기, 결함 문장에 있어야 할 글자) — 막아야 할 것."""
    D = lambda docs: docs["declared_assumptions"]["default"]  # noqa: E731
    E = lambda docs: docs["equipment_taxonomy"]["default"]  # noqa: E731
    return [
        ("measure alias on two measures", lambda d: d["measure_cost_catalog"]["default"]["measures"]["LED"]["aliases_ko"].append("창문"), "창문"),
        ("measure alias = other measure code", lambda d: d["measure_cost_catalog"]["default"]["measures"]["RCX"]["aliases_ko"].append("led"), "RCX · LED"),
        ("equipment alias on two kinds", lambda d: E(d)["aliases_ko"]["plug"].append("조명"), "조명"),
        ("equipment alias spacing variant on another kind", lambda d: E(d)["aliases_ko"]["plug"].append("냉난 방기"), "냉난 방기"),
        ("aliases_ko kind not in capability_matrix", lambda d: E(d)["aliases_ko"].update(heat_pump=["히트펌프실"]), "heat_pump"),
        ("labels_ko kind not in capability_matrix", lambda d: E(d)["labels_ko"].update(heat_pump={"name_ko": "x", "aliases_ko": []}), "heat_pump"),
        ("labels_ko drops a channel alias", lambda d: E(d)["labels_ko"]["refrigeration"]["aliases_ko"].remove("쇼케이스"), "쇼케이스"),
        ("labels_ko name on two kinds", lambda d: E(d)["labels_ko"]["meter"].update(name_ko="냉각탑"), "냉각탑"),
        ("dr_class unknown class", lambda d: E(d)["dr_class"]["by_kind"].update(lighting="shed"), "shed"),
        ("dr_class unknown kind", lambda d: E(d)["dr_class"]["by_kind"].update(heat_pump="keep"), "heat_pump"),
        ("dr_class share_ref to a missing row", lambda d: E(d)["dr_class"]["classes"]["limit"].update(share_ref="declared_assumptions.nope"), "nope"),
        ("asset alias on two kinds", lambda d: d["target_vocabulary"]["default"]["air_asset_kinds"]["HOM"]["aliases_ko"].append("가게"), "가게"),
        ("asset alias = other kind's label", lambda d: d["target_vocabulary"]["default"]["air_asset_kinds"]["RET"]["aliases_ko"].append("건물"), "건물"),
        ("class word alias on two words", lambda d: d["data_classification"]["default"]["classification"]["words"]["imputed"].update(aliases_ko=["근사"]), "근사"),
        ("facility classification not a word", lambda d: D(d)["facility_use_classes"]["value"]["cooling_shelter_candidate"].update(classification="guess"), "guess"),
        ("facility use code malformed", lambda d: D(d)["facility_use_classes"]["value"]["cooling_shelter_candidate"].update(uses=["1410"]), "1410"),
        ("facility without codes", lambda d: D(d)["facility_use_classes"]["value"]["cooling_shelter_candidate"].update(uses=[], use_prefixes=[]), "비었다"),
        ("facility name on two classes", lambda d: D(d)["facility_use_classes"]["value"].update(
            library={"label_ko": "도서관", "names_ko": ["쉼터"], "uses": ["10100"], "classification": "estimated"}), "쉼터"),
        ("delivery profile without a name", lambda d: D(d)["comm_status_thresholds"]["by_delivery"]["hourly_realtime"].pop("label_ko"), "hourly_realtime"),
        ("two profiles with one name", lambda d: D(d)["comm_status_thresholds"]["by_delivery"]["hourly_realtime"].update(label_ko="일 배치"), "일 배치"),
        ("event noun in two lists", lambda d: D(d)["schedule_event_nouns"]["value"]["nouns_needing_date_word"].append("행사"), "행사"),
        ("event noun twice", lambda d: D(d)["schedule_event_nouns"]["value"]["nouns"].append("축 제"), "축제"),
        ("critic family also in the old row", lambda d: D(d)["debate_family_critics"]["value"].update(pareto=["data"]), "pareto"),
        ("critic name unknown", lambda d: D(d)["debate_family_critics"]["value"]["audit"].append("finance"), "finance"),
        ("demo replacement measure unknown", lambda d: D(d)["demo_user_answers"]["value"].update(replacement_measure_code="FRIDGE"), "FRIDGE"),
        ("climate shift end use unknown", lambda d: D(d)["climate_load_shift"]["value"]["ssp245_2050"].update(cooling_gas=1.1), "cooling_gas"),
        ("hazard scenario for an undeclared hazard", lambda d: D(d)["hazard_week_scenarios"]["value"].update(flood=[{"id": "a", "offset_c": 0}]), "flood"),
        ("signature op unknown", lambda d: d["ems_strategies"]["default"]["strategies"]["M16"]["observable_signature"].update(op="between"), "between"),
        ("signature metric on two strategies", lambda d: d["ems_strategies"]["default"]["strategies"]["M16"]["observable_signature"].update(
            metric="night_to_day_ratio"), "night_to_day_ratio"),
        ("season system without spring/autumn", lambda d: d["calendar_conventions"]["default"].update(question_season_system="kepco_tariff"), "spring"),
        ("season system without a season table", lambda d: d["calendar_conventions"]["default"].update(question_season_system="heating_season"), "heating_season"),
        ("season system unknown", lambda d: d["calendar_conventions"]["default"].update(question_season_system="lunar"), "lunar"),
    ]


def test_vocabulary_gate_blocks_what_it_must():
    base = vg._load_dir(SCHEMAS)
    blocked = 0
    for name, mutate, needle in _mutations():
        docs = copy.deepcopy(base)
        mutate(docs)
        problems, checks = vg.problems(docs)
        assert checks > 0 and any(needle in p for p in problems), (name, problems)
        blocked += 1
    assert blocked == len(_mutations()) == 32


def test_vocabulary_gate_lets_through_what_it_must():
    """막으면 안 되는 것: 같은 열쇠 안의 띄어쓰기 변형 · 계절 체계 미정(null — 소비처가 되묻는다) · 새 종류의 새 이름."""
    base = vg._load_dir(SCHEMAS)
    passed = 0
    for mutate in (lambda d: d["equipment_taxonomy"]["default"]["aliases_ko"]["ahu"].append("공조 기"),
                   lambda d: d["equipment_taxonomy"]["default"]["labels_ko"]["ahu"]["aliases_ko"].append("공조 기"),
                   lambda d: d["calendar_conventions"]["default"].update(question_season_system=None),
                   lambda d: d["declared_assumptions"]["default"]["facility_use_classes"]["value"].update(
                       library={"label_ko": "도서관 후보", "names_ko": ["도서관"], "uses": ["10100"], "classification": "estimated"}),
                   lambda d: d["measure_cost_catalog"]["default"]["measures"]["LED"]["aliases_ko"].append("L E D 조명 교체")):
        docs = copy.deepcopy(base)
        mutate(docs)
        problems, checks = vg.problems(docs)
        assert problems == [] and checks > 0, problems
        passed += 1
    assert passed == 5
    assert vg.problems({}) == ([], 0)                    # 문서가 없으면 검사 0건 — 부르는 쪽이 사고로 센다(아래)


def test_generator_and_validator_refuse_a_broken_vocabulary(monkeypatch, tmp_path):
    """적재 때 막는다 — 생성기는 결함·검사 0건이면 만들지 않고, 검증기는 같은 함수로 위반을 낸다(양쪽)."""
    gc.load_schemas()                                    # 지금 스키마는 통과(반대쪽)
    assert vs.check_declared_vocabularies() == []
    for fake in ((["'x' → a · b"], 5), ([], 0)):
        monkeypatch.setattr(vg, "problems_in_dir", lambda _d, fake=fake: fake)
        with pytest.raises(ValueError):
            gc.load_schemas()
    monkeypatch.undo()
    broken = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, broken)
    doc = json.loads((broken / "measure_cost_catalog.json").read_text(encoding="utf-8"))
    doc["default"]["measures"]["LED"]["aliases_ko"].append("창문")
    (broken / "measure_cost_catalog.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    out = vs.check_declared_vocabularies(broken)
    assert out and any("창문" in line for line in out), out
    assert vs.check_declared_vocabularies(tmp_path / "empty") == ["선언 어휘 검사 0건 — 검사가 돌지 않았다(통과 아님)"]


# ── ④ 질문 계절 체계 ────────────────────────────────────────────────────────────────────────────────────────
def test_question_season_system_resolves_all_four_seasons():
    cal = _load("calendar_conventions.json")["default"]
    chosen = cal["question_season_system"]
    seasons = cal["season_systems"][chosen]["seasons"]
    assert chosen == "meteorological"
    assert seasons == {"spring": [3, 4, 5], "summer": [6, 7, 8], "autumn": [9, 10, 11], "winter": [12, 1, 2]}
    assert sorted(m for ms in seasons.values() for m in ms) == list(range(1, 13))
    # 계절 넷을 모두 가진 체계는 이것 하나다(결정의 근거를 값으로) — 요금 계절은 봄·가을이 한 칸
    four = [n for n, s in cal["season_systems"].items() if set((s.get("seasons") or {})) >= {"spring", "summer", "autumn", "winter"}]
    assert four == ["meteorological"], four
    assert sorted(cal["season_systems"]["kepco_tariff"]["seasons"]["summer"]) == seasons["summer"]   # 여름은 두 체계가 같다
    assert "meteorological" in cal["question_season_system_basis"] and "결정" in cal["question_season_system_basis"]


# ── ⑤ 생성본 도달 ──────────────────────────────────────────────────────────────────────────────────────────
def test_new_rows_reach_the_generated_constants():
    schemas = gc.load_schemas()
    full = gc.gen_python(schemas)
    ns: dict = {}
    exec(full, ns)
    decl = ns["DECLARED_ASSUMPTIONS"]
    assert all(k in decl for k in NEW_ROWS_0372) and decl == _declared()
    assert decl["hazard_week_scenarios"]["value"]["cold"] and decl["serving_display_limits"]["value"]["presentation_table_max_columns"] == 12
    assert ns["STRATEGIES"]["M10"]["observable_signature"]["high"] == 0.7
    assert ns["AXIS_CITIES"]["C09"]["coastal"] is True and ns["AXIS_CITIES"]["C01"]["coastal"] is False
    assert ns["AIR_ASSET_KINDS"]["RET"]["aliases_ko"] == ["매장", "가게", "지점"]
    assert ns["DATA_CLASSIFICATION_VOCAB"]["words"]["estimated"]["aliases_ko"] == ["근사", "범위"]
    assert ns["JUDGEMENT_THRESHOLDS"]["anomaly"]["robust_z"]["value"] == 3.5
    assert ns["CALENDAR_CONVENTIONS"]["question_season_system"] == "meteorological"
    checked = 0
    for project in ("8sim-shared", "agentleague", "building-energy-3d", "airos-energy-decision"):
        got: dict = {}
        exec(gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS[project]), got)
        assert all(k in got["DECLARED_ASSUMPTIONS"] for k in NEW_ROWS_0372), project
        checked += 1
    al: dict = {}
    exec(gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS["agentleague"]), al)
    assert al["DECLARED_ASSUMPTIONS"]["debate_family_critics"]["value"]["audit"] == ["data", "legal"]
    ts = gc.apply_exports_filter(gc.gen_typescript(schemas), "ts", gc.PROJECT_TARGETS["building-energy-3d"])
    assert '"presentation_chart_max_series"' in ts and '"debate_axis_scales"' in ts
    assert checked == 4


# ── ⑥ 값을 가리키는 행 · 넣지 않은 요청 ─────────────────────────────────────────────────────────────────────
def test_new_rows_agree_with_what_they_point_at():
    d = _declared()
    eq = _load("equipment_taxonomy.json")
    cap = set(eq["default"]["capability_matrix"])
    checked = 0
    assert d["drop_integrity_rule"]["value"]["daily_rows_min"] == d["drop_reference_days_default"]["value"]; checked += 1
    assert d["debate_calendar"]["value"]["hours_per_year"] == 365 * 24 == _load("simulation_channels.json")["default"]["expected_hours"][0]; checked += 1
    heat, cold = d["hazard_week_scenarios"]["value"]["heat"], d["hazard_week_scenarios"]["value"]["cold"]
    assert [r["id"] for r in heat] == [r["id"] for r in cold] and [r["offset_c"] for r in cold] == [-r["offset_c"] for r in heat]; checked += 1
    assert d["hazard_days"]["cold"]["comparison"] == "daily_min_le"; checked += 1        # 한파 = 문턱 아래로(음의 오프셋이 더 춥다)
    catalog = _load("measure_cost_catalog.json")["default"]["measures"]
    assert catalog[d["demo_user_answers"]["value"]["replacement_measure_code"]]["measure_class"] == "equipment_replacement"; checked += 1
    shift = d["climate_load_shift"]["value"]
    assert shift["ssp245_2050"]["cooling_elec"] < shift["ssp585_2050"]["cooling_elec"] < shift["ssp585_2080"]["cooling_elec"]; checked += 1
    assert set(eq["default"]["labels_ko"]) == cap; checked += 1                             # 이름표가 종류 전부를 덮는다
    dr = eq["default"]["dr_class"]
    assert dr["by_end_use"] == {"lights_kw": "curtailable", "cooling_kw": "limit", "fans_kw": "keep", "equipment_kw": "keep"}; checked += 1
    assert dr["by_kind"]["refrigeration"] == "keep" and "DR 제외" in eq["$defs"]["EquipmentKind"]["description"]; checked += 1
    assert set(dr["by_kind"]) <= cap and "boiler" not in dr["by_kind"]; checked += 1      # 선언 없는 종류는 유지로 짓지 않는다
    sig = _load("ems_strategies.json")["default"]["strategies"]["M10"]["observable_signature"]
    assert sig["high"] > sig["threshold"]; checked += 1
    assert d["policy_adverse_boundary"]["value"] == 0 and d["policy_adverse_boundary"]["comparison"] == "strictly_less"; checked += 1
    assert set(d["debate_family_critics"]["value"]).isdisjoint(d["debate_default_personas"]["value"]["critics_by_family"]); checked += 1
    assert checked == 13


def test_declined_requests_did_not_become_rows():
    """넣지 않은 요청(EC 아님 · 값 없음)은 행이 없다 — 소비처의 이름 있는 거절·env 경로가 그대로 선다."""
    d = _declared()
    for key in ("review_task_roles", "judge_calibration_agreement_min", "judge_calibration_set_size", "storage_capex_krw_per_kwh"):
        assert key not in d, key
    assert all("new_saving_share_range" not in dev for dev in d["home_appliance_replacement"]["value"]["devices"])
    models = _load("ai_model_registry.json")["default"]["models"]
    assert models and all("training_domain" not in m for m in models.values())


def test_generated_models_follow_the_new_enum_and_fields():
    from pydantic import ValidationError
    from energy_contracts._pydantic_models import airo_result, error_response, interface_types
    from energy_contracts._pydantic_models.measure_cost_catalog import Measures
    for mod in (error_response, airo_result, interface_types):
        assert "later" in {m.value for m in mod.Retry}, mod.__name__
    entry = _load("measure_cost_catalog.json")["default"]["measures"]["WIN"]
    assert [a.root for a in Measures.model_validate(entry).aliases_ko] == ["창문", "유리창", "이중창", "삼중창"]
    with pytest.raises(ValidationError):
        error_response.Refusal.model_validate({"code": "X_Y", "kind": "internal", "message_ko": "m", "retry": "soon"})
    assert error_response.Refusal.model_validate({"code": "X_Y", "kind": "internal", "message_ko": "m", "retry": "later"})
