# -*- coding: utf-8 -*-
"""0.3.70 (2026-09-30) — declared_assumptions 1.3 · judgement_thresholds 1.1 · error_response 1.2 · certified_tests 1.0.

코드 리터럴로 있던 선언 기본값을 정본으로 옮겼다(가산). 검사마다 반례 양쪽 — 받아야 할 것 · 막아야 할 것 — 을 걸고,
검사가 실제로 돈 건수를 단언한다(0 건은 통과가 아니다). 같은 값이 두 정본에 있지 않은지는 값이 아니라 **가리킴**으로 본다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))

import gen_constants as gc  # noqa: E402

BASIS_KINDS = {"moved_literal", "declared_demo_assumption", "standard_citation", "derived_from_ec"}
REQUIRED = ("id", "value", "label_ko", "rule_ko", "classification", "basis_kind", "basis", "source")


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _declared() -> dict:
    return _load("declared_assumptions.json")["default"]


def _units() -> set[str]:
    return set(_load("interface_types.json")["$defs"]["QuantityUnit"]["enum"])


def row_problems(key: str, row: dict, units: set[str]) -> list[str]:
    """1.3 형식 행 하나의 결함 목록(빈 목록 = 온전). 시험과 반례가 같은 함수를 쓴다."""
    out = [f"{key}: {f} 없음" for f in REQUIRED if row.get(f) in (None, "")]
    if row.get("id") != key:
        out.append(f"{key}: id != 키")
    if row.get("classification") not in ("declared", "assumed"):
        out.append(f"{key}: classification={row.get('classification')!r}")
    if row.get("basis_kind") not in BASIS_KINDS:
        out.append(f"{key}: basis_kind={row.get('basis_kind')!r}")
    if ("unit" in row) == ("unit_text" in row):
        out.append(f"{key}: unit · unit_text 중 정확히 하나여야 한다")
    if "unit" in row and row["unit"] not in units:
        out.append(f"{key}: unit={row['unit']!r} 는 QuantityUnit 낱말이 아니다")
    return out


def _new_rows() -> dict[str, dict]:
    return {k: v for k, v in _declared().items() if isinstance(v, dict) and "basis_kind" in v}


# ── 새 행의 모양 ───────────────────────────────────────────────────────────────────────────────────────────────
def test_new_rows_carry_value_unit_label_basis_and_class():
    rows, units = _new_rows(), _units()
    problems = [p for k, r in rows.items() for p in row_problems(k, r, units)]
    assert not problems, problems
    assert len(rows) == 54, len(rows)          # 검사 54 건(0 건이면 그것이 사고다)
    # 근거 없는 값은 '선언 시연 가정' 이라고 스스로 적는다 — 표준인 척하지 않는다
    demo = [k for k, r in rows.items() if r["basis_kind"] == "declared_demo_assumption"]
    assert demo and all("선언" in rows[k]["basis"] or "가정" in rows[k]["basis"] for k in demo), \
        [k for k in demo if "선언" not in rows[k]["basis"] and "가정" not in rows[k]["basis"]]


def test_row_check_blocks_what_it_must():
    units = _units()
    good = copy.deepcopy(_new_rows()["setpoint_step_c"])
    assert row_problems("setpoint_step_c", good, units) == []
    for mutate in (lambda r: r.pop("basis"), lambda r: r.update(classification="measured"),
                   lambda r: r.update(unit="%"), lambda r: r.update(unit_text="x"), lambda r: r.update(id="other"),
                   lambda r: r.update(basis_kind="standard"), lambda r: r.pop("value")):
        bad = copy.deepcopy(good)
        mutate(bad)
        assert row_problems("setpoint_step_c", bad, units), mutate


def test_rows_of_1_2_keep_their_values():
    d = _declared()
    assert d["ranked_rows_top_n_default"]["value"] == 10
    assert d["top_share_pct_default"]["value"] == 25.0
    assert d["quick_payback_max_yr_default"]["value"] == 3.0
    assert d["aging_years_default"]["value"] == 30
    assert d["coldwave_design_days"]["value"] == 5
    assert d["switchable_cut_share_default"]["value"] == 0.5
    assert d["hazard_days"]["heat"]["threshold_c"] == 33.0 and d["hazard_days"]["heat"]["months"] == [6, 9]
    old = [k for k, v in d.items() if isinstance(v, dict) and "basis_kind" not in v]
    assert len(old) == 16, old                 # 1.2 의 16행은 그대로(이름도)


# ── 같은 값이 두 정본에 있지 않다 — 가리키거나, 같은지 시험으로 묶는다 ──────────────────────────────────────────
def test_new_rows_agree_with_the_values_they_point_at():
    d = _declared()
    ems = _load("ems_strategies.json")["default"]
    cat = _load("measure_cost_catalog.json")["default"]
    thr = _load("judgement_thresholds.json")["default"]
    measures = cat["measures"]
    codes = set(measures) if isinstance(measures, dict) else {m["code"] for m in measures}
    rows = measures if isinstance(measures, dict) else {m["code"]: m for m in measures}
    checked = 0
    # 수요반응 3단계의 마지막 조명 몫 = 정본 조명 제어(M17) depth
    assert d["dr_three_stage"]["value"]["light_shares"][-1] == ems["dr_assumptions"]["strategies"]["M17"]["depth"]; checked += 1
    assert len(d["dr_three_stage"]["value"]["light_shares"]) == d["dr_three_stage"]["value"]["stage_count"]; checked += 1
    assert d["dr_three_stage"]["value"]["cooling_strategy"] in ems["strategies"]; checked += 1
    assert d["dr_default_shed_strategy"]["value"] in ems["dr_assumptions"]["strategies"]; checked += 1
    # 기준안·폭염 기본 전략은 정본 전략 이름과 같은 전략이다
    assert ems["strategies"][d["baseline_strategy_code"]["value"]]["name_en"] == "Baseline"; checked += 1
    assert [ems["strategies"][c]["name_en"] for c in d["heatwave_policy_default_strategies"]["value"]] == \
        ["PMV_Relaxed", "DemandResponse"]; checked += 1
    # 투자 구간의 운영 개선 문턱 = 정본 조치 목록의 운영 개선 조치 최대 단가
    op_max = max(float(m["capex_krw_per_m2"]) for m in rows.values() if m["measure_class"] == "operational")
    assert d["investment_tiers"]["value"]["operational_max_krw_per_m2"] == op_max; checked += 1
    assert d["investment_tiers"]["value"]["small_repair_max_krw_per_m2"] >= op_max; checked += 1
    assert set(d["retrofit_difficulty"]["value"]["by_measure_class"]) == {m["measure_class"] for m in rows.values()}; checked += 1
    # 조치 코드는 정본 조치 목록 안에 있다
    pack = d["measure_packages"]["value"]["green_remodeling"]
    used = set(pack["required"]) | set(pack["optional"]) | {c for group in pack["optional_one_of"] for c in group}
    assert used <= codes and d["cohort_policy_virtual"]["value"]["measure_code"] in codes; checked += 1
    assert all(dev["life_catalog_code"] in codes for dev in d["home_appliance_replacement"]["value"]["devices"]
               if dev["life_catalog_code"]); checked += 1
    # 다른 행을 가리키는 칸은 실제 행을 가리킨다(새 수 없음)
    assert d["life_roadmap"]["value"]["early_replacement_payback_max_yr_ref"] in d; checked += 1
    assert d["budget_bundle_thresholds"]["value"]["quick_payback_max_yr_ref"] in d; checked += 1
    for group in d["portfolio_triage"]["value"]["groups"]:
        ref = group.get("threshold_ref")
        if ref:
            schema, concept, name = ref.split(".")
            assert schema == "judgement_thresholds" and "value" in thr[concept][name], ref; checked += 1
    assert d["precool_delta_c"]["value"] == d["setpoint_step_c"]["value"]; checked += 1
    assert cat["method"]["discount_rate_default"] in d["discount_rate_grid_default"]["value"]; checked += 1
    assert all(r > 0 for r in d["discount_rate_grid_default"]["value"]); checked += 1
    # 토론: Pareto 쾌적 제약 = 임차인 수용 문턱(같은 값이라고 적었다)
    assert d["debate_virtual_effect"]["value"]["pareto_comfort_limit_h"] == \
        d["debate_role_rules"]["value"]["tenant.comfort_accept_h"]; checked += 1
    assert all(lo <= hi for lo, hi, *_ in d["debate_assumption_ranges"]["value"].values()); checked += 1
    assert len(d["debate_assumption_ranges"]["value"]) == 30; checked += 1
    # 화면 상한: 패널 목표는 장면 저장 한도 안
    lim = d["serving_display_limits"]["value"]
    assert lim["panel_value_target_bytes"] < lim["scene_payload_max_bytes"] == 64 * 1024; checked += 1
    # 폭염 기준 창은 폭염 창 안
    heat = d["hazard_days"]["heat"]
    assert heat["months"][0] <= heat["baseline_months"][0] and heat["baseline_months"][1] <= heat["months"][1]; checked += 1
    # PMV 가정: 계절 넷 전부 · 대사량은 하나
    assert set(d["pmv_inputs"]["value"]["clo_by_season"]) == {"summer", "winter", "spring", "autumn"}; checked += 1
    assert abs(sum(d["end_use_split_default"]["shares"].values()) - 1.0) < 1e-9; checked += 1
    assert checked >= 24, checked


def test_existing_canonical_thresholds_were_not_duplicated():
    """이미 정본에 있는 값(이상 z · 순위 기본 개수 · 상위 비율)에 새 행을 만들지 않았다 — 코드가 기존 행을 읽는다."""
    d, thr = _declared(), _load("judgement_thresholds.json")["default"]
    assert thr["anomaly"]["residual_z"]["value"] == 3.0 and thr["anomaly"]["screening_z"]["value"] == 2.0
    names = " ".join(d)
    for forbidden in ("robust_z", "anomaly_z", "deviation_z", "policy_target_top_share", "top_n_default_by_tool"):
        assert forbidden not in names, forbidden
    top_n_rows = [k for k in d if "top_n" in k]
    assert top_n_rows == ["ranked_rows_top_n_default", "action_shortlist_top_n_default"], top_n_rows
    assert "target_top_share" not in d["cohort_policy_virtual"]["value"]      # 상위 비율은 top_share_pct_default 하나


def test_judgement_thresholds_1_1_additions():
    t = _load("judgement_thresholds.json")
    thr = t["default"]
    assert t["version"] == "1.1"
    assert thr["anomaly"]["monthly_screening_min_months"]["value"] == 6
    assert thr["anomaly"]["band_out_share_multiple"]["value"] == 2.0
    assert thr["anomaly"]["sustained_out_hours"]["value"] == 3
    assert thr["comfort"]["pmv_out_of_band_increase"]["value"] == 0.10
    sens = thr["temperature_sensitivity"]
    assert sens["min_observed_temperature_days"]["value"] == 30 and 0 < sens["min_r2"]["value"] < 1
    added = [thr["anomaly"]["monthly_screening_min_months"], thr["anomaly"]["band_out_share_multiple"],
             thr["anomaly"]["sustained_out_hours"], thr["comfort"]["pmv_out_of_band_increase"],
             sens["min_observed_temperature_days"], sens["min_r2"]]
    assert all(a["classification"] == "assumed" and a["source"] and a["rule_ko"] for a in added) and len(added) == 6


# ── 공인 시험 · 오류 코드 ──────────────────────────────────────────────────────────────────────────────────────
def test_certified_tests_carry_only_certificate_values():
    c = _load("certified_tests.json")["default"]
    load = c["load_forecast"]
    for field in ("certificate", "cvrmse_public_pct", "public_scope", "cvrmse_korea_pct", "korea_scope", "scope_note", "source"):
        assert load[field] not in (None, ""), field
    assert (load["cvrmse_public_pct"], load["cvrmse_korea_pct"]) == (12.91, 12.55)
    assert load["cvrmse_public_pct"] <= load["criterion_pct_max"] and load["cvrmse_korea_pct"] <= load["criterion_pct_max"]
    assert all(t["classification"] == "certified" and t["certificate"] and t["source"] for t in c.values()) and len(c) == 3
    # 막아야 할 것: 자체 검증값(12.93 — 성적서에 없다)이 수 칸으로 실리면 안 된다. 주의 문장 안의 글자는 허용(금지 사실의 고지)
    numbers = [v for t in c.values() for v in t.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    assert numbers and 12.93 not in numbers
    assert "12.93" in load["scope_note"] and "공인 라벨" in load["scope_note"]
    # 정본 표에 없는 값은 null 과 사유
    assert c["nl_diagnosis"]["sample_scope"] is None and "null" in c["nl_diagnosis"]["scope_note"]


def test_payload_too_large_is_a_validation_code():
    e = _load("error_response.json")
    assert e["version"] == "1.2"
    assert e["default"]["codes"]["PAYLOAD_TOO_LARGE"] == {"status": 413, "title": "Payload too large", "category": "validation"}
    assert e["default"]["codes"]["VALIDATION_FAILED"]["status"] == 422          # 옛 코드는 그대로
    assert len(e["default"]["codes"]) == 16


def test_calendar_week_starts_on_monday():
    week = _load("calendar_conventions.json")["default"]["week"]
    assert week["start_weekday"] == "MON" and week["days"][0] == "MON" and len(week["days"]) == 7 and week["source"]


# ── 생성기는 목록을 손으로 적지 않는다 — 스키마 표 전체가 생성본에 닿는다 ─────────────────────────────────────
def test_generator_derives_whole_tables_and_new_rows_reach_every_consumer():
    schemas = gc.load_schemas()
    full = gc.gen_python(schemas)
    ns: dict = {}
    exec(full, ns)
    assert ns["DECLARED_ASSUMPTIONS"] == _declared()
    assert ns["CERTIFIED_TESTS"] == _load("certified_tests.json")["default"]
    assert ns["ERROR_CODES"] == _load("error_response.json")["default"]["codes"]
    assert ns["JUDGEMENT_THRESHOLDS"] == _load("judgement_thresholds.json")["default"]
    assert ns["CALENDAR_CONVENTIONS"]["week"]["start_weekday"] == "MON"
    ts = gc.gen_typescript(schemas)
    assert "export const DECLARED_ASSUMPTIONS = " in ts and '"display_tier_alpha"' in ts
    # 소비처 화이트리스트: 새 표를 읽어야 하는 곳에 실제로 실린다 / 읽지 않는 곳에는 실리지 않는다(양쪽)
    reach = {"8sim-shared": ("DECLARED_ASSUMPTIONS", "CERTIFIED_TESTS", "JUDGEMENT_THRESHOLDS", "CALENDAR_CONVENTIONS"),
             "agentleague": ("DECLARED_ASSUMPTIONS", "CERTIFIED_TESTS", "JUDGEMENT_THRESHOLDS", "ERROR_CODES"),
             "building-energy-3d": ("DECLARED_ASSUMPTIONS", "ERROR_CODES", "JUDGEMENT_THRESHOLDS"),
             "airos-energy-decision": ("DECLARED_ASSUMPTIONS", "JUDGEMENT_THRESHOLDS")}
    checked = 0
    for project, names in reach.items():
        out = gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS[project])
        got: dict = {}
        exec(out, got)
        for name in names:
            assert name in got, (project, name)
            checked += 1
    assert checked == 13
    be3d_ts = gc.apply_exports_filter(ts, "ts", gc.PROJECT_TARGETS["building-energy-3d"])
    assert "export const DECLARED_ASSUMPTIONS = " in be3d_ts
    edge: dict = {}
    exec(gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS["edge-agent"]), edge)
    assert "DECLARED_ASSUMPTIONS" not in edge and "CERTIFIED_TESTS" not in edge
    assert edge["ERROR_CODES"]["PAYLOAD_TOO_LARGE"]["status"] == 413
