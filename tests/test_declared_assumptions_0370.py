# -*- coding: utf-8 -*-
"""0.3.70 (2026-09-30) — declared_assumptions 1.3 · judgement_thresholds 1.1 · error_response 1.2 · certified_tests 1.0.

코드 리터럴로 있던 선언 기본값을 정본으로 옮겼다(가산). 검사마다 반례 양쪽 — 받아야 할 것 · 막아야 할 것 — 을 걸고,
검사가 실제로 돈 건수를 단언한다(0 건은 통과가 아니다). 같은 값이 두 정본에 있지 않은지는 값이 아니라 **가리킴**으로 본다.

0.3.71 (2026-09-30) — GPT 상의 반영(declared_assumptions 1.4 · judgement_thresholds 1.2 · measure_cost_catalog 1.3): 여섯 값에 새 칸,
인용 셋 문구, 조치마다 work_scope. 이미 이 행을 import 하는 코드가 있어 **가산**이어야 한다 — 0.3.70 태그의 파일과 키·값을 맞대 본다.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

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
    # 근거(2026-09-30, 0.3.72): 새 행 33(요청 C1~C11 · WP6 R10 — 이름 목록 = test_declared_assumptions_0372.NEW_ROWS_0372) 도 같은 모양 규칙을
    #   지킨다. 0.3.70 의 54 행이 그대로인지는 0.3.72 시험의 태그 대조가 본다(반대쪽).
    assert len(rows) == 54 + 33, len(rows)     # 검사 87 건(0 건이면 그것이 사고다)
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
    # 근거(2026-09-30, 0.3.71): 1.1 → 1.2 는 가산(temperature_sensitivity 두 행에 basis_kind·basis·표시 칸 — 값 그대로, $comment 1.2 절).
    # 1.1 가산분의 값은 아래 단언이 그대로 지킨다.
    # 근거(2026-09-30, 0.3.72): 1.2 → 1.3 은 가산(anomaly.robust_z — 요청 C2, 스키마 $comment 1.3 절). 1.2 의 값이 그대로인지는
    #   0.3.72 시험의 태그 대조가 본다(반대쪽).
    assert t["version"] == "1.3"
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
    # 근거(2026-09-30, 0.3.72): 1.2 → 1.3 은 가산(Refusal.retry 열거 += later — 요청 C2). 코드 표는 그대로(아래 16개).
    assert e["version"] == "1.3"
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


# ══ 0.3.71 (2026-09-30) — GPT 상의 반영: 근거 없이 정한 여섯 값 · 인용 셋 · 조치의 공사 범위 ════════════════════════
#: 사용자 지시 2026-09-30 19:24 "지피티와 상의해서 정해" — 결정 기록 = 캠페인 review_exchange/rounds/R079_gpt.md.
#: (정본 파일, 행 경로) — 여섯 값은 표준값이 아니다(선언 시연 가정 그대로) · 인용 셋은 웹 대조로 문구를 고쳤다.
DEMO_ROWS_0371 = (("declared_assumptions.json", ("short_cycling",)),
                  ("declared_assumptions.json", ("comm_status_thresholds",)),
                  ("declared_assumptions.json", ("life_roadmap",)),
                  ("declared_assumptions.json", ("investment_tiers",)),
                  ("declared_assumptions.json", ("precool_delta_c",)),
                  ("judgement_thresholds.json", ("temperature_sensitivity", "min_observed_temperature_days")))
CITED_ROWS_0371 = (("judgement_thresholds.json", ("temperature_sensitivity", "min_r2")),
                   ("declared_assumptions.json", ("pmv_inputs",)))
#: 문구(사람이 읽는 칸)는 바뀌어도 된다 — 그 밖의 잎(수·코드·참조 이름)은 바뀌면 가산이 아니다.
TEXT_KEYS = {"label_ko", "rule_ko", "basis", "source", "note", "description", "$comment", "updated", "version", "title"}


def _row(name: str, path: tuple[str, ...]) -> dict:
    node = _load(name)["default"]
    for part in path:
        node = node[part]
    return node


def consulted_row_problems(row: dict, *, cited: bool) -> list[str]:
    """0.3.71 에 검토한 행 하나의 근거 표기 결함(빈 목록 = 온전). 시험과 반례가 같은 함수를 쓴다."""
    basis = str(row.get("basis") or "")
    out = []
    if not basis:
        out.append("basis 없음")
    if "원문 대조 전" in basis:
        out.append("'원문 대조 전' 이 남았다")
    if cited:
        if row.get("basis_kind") != "standard_citation":
            out.append(f"basis_kind={row.get('basis_kind')!r} (인용 행)")
        if "웹 대조 2026-09-30" not in basis:
            out.append("웹 대조 날짜 없음")
    else:
        # 표준이 없는 값 — GPT 와 상의했어도 표준 인용으로 올리지 않는다
        if row.get("basis_kind") != "declared_demo_assumption":
            out.append(f"basis_kind={row.get('basis_kind')!r} (선언 가정 행)")
        if not ("GPT 상의" in basis and "2026-09-30" in basis):
            out.append("GPT 상의 기록 없음")
        if "선언" not in basis and "가정" not in basis:
            out.append("선언 가정이라고 적지 않았다")
    if row.get("classification") != "assumed":
        out.append(f"classification={row.get('classification')!r}")
    return out


def additive_problems(old, new, path: str = "") -> tuple[list[str], int]:
    """old 의 키가 new 에 모두 있고 문구 아닌 잎이 같은가(새 키는 허용). → (결함 목록, 대조한 잎 수)."""
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [f"{path}: dict 가 아니게 됐다"], 0
        out, n = [], 0
        for key, value in old.items():
            if key not in new:
                out.append(f"{path}/{key}: 키가 사라졌다")
            elif key not in TEXT_KEYS:
                sub, k = additive_problems(value, new[key], f"{path}/{key}")
                out += sub
                n += k
        return out, n
    if isinstance(old, list) and any(isinstance(v, dict) for v in old):
        if not isinstance(new, list) or len(new) != len(old):
            return [f"{path}: 목록 길이가 바뀌었다"], 0
        out, n = [], 0
        for i, (a, b) in enumerate(zip(old, new)):
            sub, k = additive_problems(a, b, f"{path}[{i}]")
            out += sub
            n += k
        return out, n
    return ([] if old == new else [f"{path}: {old!r} -> {new!r}"]), 1


def _at_tag(tag: str, name: str) -> dict | None:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "show", f"{tag}:energy_contracts/schemas/{name}"],
                             capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return json.loads(out.stdout.decode("utf-8"))


def test_0371_additive_against_the_0370_tag():
    """0.3.70 에서 소비처가 import 한 표가 그대로다 — 키가 사라지거나 수·코드가 바뀌면 실패(문구는 허용)."""
    checked = 0
    for name in ("declared_assumptions.json", "judgement_thresholds.json", "measure_cost_catalog.json"):
        old = _at_tag("v0.3.70", name)
        if old is None:
            pytest.skip(f"[해당 없음] git 태그 v0.3.70 을 못 읽었다({name}) — 통과가 아니다. 아래 고정값 시험이 대신 본다")
        problems, n = additive_problems(old["default"], _load(name)["default"])
        assert not problems, (name, problems)
        checked += n
    assert checked > 500, checked                       # 세 표의 잎 전부(0 건이면 그것이 사고다)


def test_0371_additive_check_blocks_what_it_must():
    old = {"a": {"value": {"x": 1, "ref": "k"}, "rule_ko": "옛 문장"}, "rows": [{"c": 1}]}
    same = copy.deepcopy(old)
    same["a"]["rule_ko"] = "새 문장"                     # 문구는 바뀌어도 된다
    same["a"]["new_key"] = [0.25, 0.75]                 # 새 칸은 된다
    assert additive_problems(old, same) == ([], 3)
    for mutate in (lambda d: d["a"]["value"].pop("x"), lambda d: d["a"]["value"].update(x=2),
                   lambda d: d["a"]["value"].update(ref="other"), lambda d: d.pop("rows"),
                   lambda d: d["rows"][0].update(c=5), lambda d: d["rows"].append({"c": 2})):
        bad = copy.deepcopy(old)
        mutate(bad)
        assert additive_problems(old, bad)[0], mutate


def test_0371_existing_keys_and_values_unchanged():
    """태그를 못 읽는 곳에서도 도는 고정값 — 게이트웨이가 value 를 통째로 도구 인자로 넘기는 행(투자 구간·수명 로드맵)은
    value 의 키 집합까지 같아야 한다(도구 스키마가 additionalProperties false 라 새 칸이 value 안에 들어가면 거절된다)."""
    d, thr = _declared(), _load("judgement_thresholds.json")["default"]["temperature_sensitivity"]
    assert d["short_cycling"]["value"] == {"starts_per_day_flag": 6}
    assert d["comm_status_thresholds"]["value"] == {"ok_max_staleness_h": 24, "delayed_max_staleness_h": 72}
    assert d["life_roadmap"]["value"] == {"existing_life_used_share": 0.5, "roadmap_years": 5,
                                          "early_replacement_payback_max_yr_ref": "quick_payback_max_yr_default"}
    assert d["investment_tiers"]["value"] == {"operational_max_krw_per_m2": 6000.0, "small_repair_max_krw_per_m2": 15000.0}
    assert d["precool_delta_c"]["value"] == 1.0
    assert thr["min_observed_temperature_days"]["value"] == 30 and thr["min_r2"]["value"] == 0.75
    pmv = d["pmv_inputs"]["value"]
    assert (pmv["met"], pmv["clo_by_season"], pmv["air_speed_m_s"], pmv["mean_radiant_equals_air"]) == \
        (1.2, {"summer": 0.5, "winter": 1.0, "spring": 0.7, "autumn": 0.7}, 0.1, True)
    terms = d["debate_stated_term_ranges"]["value"]
    assert terms["lease_term_yr"]["range"] == [1, 10] and terms["budget_cycle_yr"]["range"] == [1, 1]
    # 0.3.71 은 새 행을 만들지 않았다(칸만 더했다 — 54). 근거(0.3.72): 새 행 33 을 더했다 — 이름 목록과 태그 대조는 0.3.72 시험.
    assert len(_new_rows()) == 54 + 33


def test_0371_consulted_rows_say_what_their_basis_is():
    rows = [(_row(n, p), False) for n, p in DEMO_ROWS_0371] + [(_row(n, p), True) for n, p in CITED_ROWS_0371]
    problems = [(i, consulted_row_problems(r, cited=c)) for i, (r, c) in enumerate(rows) if consulted_row_problems(r, cited=c)]
    assert not problems, problems
    assert len(rows) == 8                               # 검사 8 행 + 아래 법령 인용 2 칸
    terms = _declared()["debate_stated_term_ranges"]
    assert terms["basis_kind"] == "standard_citation" and terms["classification"] == "declared"
    lease, budget = terms["value"]["lease_term_yr"]["basis"], terms["value"]["budget_cycle_yr"]["basis"]
    for text in (lease, budget):
        assert "웹 대조 2026-09-30" in text and "원문 대조 전" not in text
    assert "제9조 제1항" in lease and "제10조 제2항" in lease and "유효함을 주장" in lease   # 임차인 예외를 빠뜨리지 않는다
    assert "국가재정법 제2조" in budget


def test_0371_basis_check_blocks_what_it_must():
    demo, cited = _row(*DEMO_ROWS_0371[0]), _row(*CITED_ROWS_0371[0])
    assert consulted_row_problems(demo, cited=False) == [] and consulted_row_problems(cited, cited=True) == []
    for row, is_cited, mutate in (
            (demo, False, lambda r: r.update(basis_kind="standard_citation")),     # 선언 가정을 표준 인용으로 올림
            (demo, False, lambda r: r.update(basis="외부 근거 없는 선언 시연 가정")),  # 상의 기록 없음
            (demo, False, lambda r: r.update(basis=r["basis"] + " 원문 대조 전")),
            (cited, True, lambda r: r.update(basis=r["basis"].replace("웹 대조 2026-09-30", ""))),
            (cited, True, lambda r: r.update(basis_kind="declared_demo_assumption")),
            (cited, True, lambda r: r.update(classification="declared"))):
        bad = copy.deepcopy(row)
        mutate(bad)
        assert consulted_row_problems(bad, cited=is_cited), mutate


def test_0371_new_keys_carry_the_decisions():
    d = _declared()
    catalog = _load("measure_cost_catalog.json")
    work_scopes = catalog["$defs"]["WorkScope"]["enum"]
    checked = 0
    # A1 — 선별 조건이지 판정이 아니다
    sc = d["short_cycling"]
    assert sc["interpretation"] == "screening_only" and "판정 아님" in sc["label_ko"] and "분 단위" in sc["rule_ko"]; checked += 1
    # A2 — 전송 주기별 문턱: 옛 value 는 일 배치 기준과 같은 값이다(파생 — 두 벌이 갈리면 실패)
    comm = d["comm_status_thresholds"]
    assert set(comm["by_delivery"]) == {"hourly_realtime", "daily_batch"}; checked += 1
    # 근거(2026-09-30, 0.3.72 · 요청 C8): 프로필마다 사람 말 이름 label_ko 칸이 생겼다(문구 칸). 파생 대조는 문턱 칸끼리 — 문턱 두 칸이
    #   옛 value 와 같고(두 벌이 갈리면 실패) 프로필의 칸은 문턱 두 칸 + 이름뿐이다(반대쪽: 문턱 칸이 늘거나 빠지면 실패).
    thresholds = lambda p: {k: v for k, v in p.items() if k != "label_ko"}  # noqa: E731
    assert thresholds(comm["by_delivery"]["daily_batch"]) == comm["value"]; checked += 1
    assert all(set(thresholds(p)) == set(comm["value"]) and p["ok_max_staleness_h"] < p["delayed_max_staleness_h"]
               for p in comm["by_delivery"].values()); checked += 1
    assert comm["by_delivery"]["hourly_realtime"]["ok_max_staleness_h"] < comm["value"]["ok_max_staleness_h"]; checked += 1
    assert comm["unknown_delivery_profile"] in comm["by_delivery"]; checked += 1
    # A3 — 세 시나리오: 중앙 가정을 사이에 둔 두 값
    road = d["life_roadmap"]
    lo, hi = road["sensitivity_life_used_shares"]
    assert 0 < lo < road["value"]["existing_life_used_share"] < hi < 1; checked += 1
    assert road["remaining_life_status_when_unknown"] == "unknown_assumed_scenarios"; checked += 1
    # A4 — 공사 범위로 가른다: 가리키는 칸이 실제로 있다 · 표시 이름이 공사 범위 낱말 전부를 덮는다
    tiers = d["investment_tiers"]
    schema_name, field = tiers["classification_basis"].split(".")
    measure_props = catalog["properties"]["measures"]["additionalProperties"]["properties"]
    assert schema_name == "measure_cost_catalog" and field in measure_props; checked += 1
    assert tiers["numeric_thresholds_role"] == "fallback_only"; checked += 1
    assert set(tiers["label_ko_by_work_scope"]) == set(work_scopes); checked += 1
    # A5 — 조건을 함께 싣는다
    pre = d["precool_delta_c"]
    assert len(pre["conditions_ko"]) == 4 and all(c.strip() for c in pre["conditions_ko"]) and "최대" in pre["label_ko"]; checked += 1
    # A6 — 예비 추정 표시
    days = _row("judgement_thresholds.json", ("temperature_sensitivity", "min_observed_temperature_days"))
    assert days["preliminary_label_below_months"] == 12 and days["preliminary_label_ko"] == "예비 추정"; checked += 1
    assert len(days["must_report_ko"]) == 2 and "추정하지 않는다" in days["rule_ko"]; checked += 1
    # B1 — 선별 기준(경험칙) · 편향·오차 기준과 구별
    r2 = _row("judgement_thresholds.json", ("temperature_sensitivity", "min_r2"))
    assert "선별 기준(경험칙)" in r2["label_ko"] and "NMBE" in r2["basis"] and "CV(RMSE)" in r2["basis"]; checked += 1
    assert checked == 15


def test_0371_every_catalog_measure_has_a_work_scope():
    """조치마다 공사 범위가 있다 — 목록을 손으로 적지 않고 카탈로그 전체에서 센다. 빠지면 스키마 검증이 실패한다(양쪽)."""
    schema = _load("measure_cost_catalog.json")
    enum = schema["$defs"]["WorkScope"]["enum"]
    measures = schema["default"]["measures"]
    assert measures and all(m.get("work_scope") in enum for m in measures.values()), \
        {k: m.get("work_scope") for k, m in measures.items() if m.get("work_scope") not in enum}
    validator = Draft202012Validator(schema)
    assert not list(validator.iter_errors(schema["default"]))
    blocked = 0
    for code in measures:                                   # 막아야 할 것: 어느 조치든 work_scope 가 빠지면
        bad = copy.deepcopy(schema["default"])
        bad["measures"][code].pop("work_scope")
        errors = list(validator.iter_errors(bad))
        assert errors and any("work_scope" in e.message for e in errors), code
        blocked += 1
    bad = copy.deepcopy(schema["default"])
    bad["measures"][next(iter(measures))]["work_scope"] = "cheap"
    assert list(validator.iter_errors(bad))
    assert blocked == len(measures) > 0
    # 생성 모델도 같은 규칙(스키마를 따라왔다)
    from pydantic import ValidationError
    from energy_contracts._pydantic_models.measure_cost_catalog import Measures
    entry = next(iter(measures.values()))
    Measures.model_validate(entry)
    with pytest.raises(ValidationError):
        Measures.model_validate({k: v for k, v in entry.items() if k != "work_scope"})


def test_0371_work_scope_agrees_with_the_definition_it_was_derived_from():
    """공사 범위 '운영' = 설비 교체가 거의 없는 조치 = 조치 분류 operational 과 같은 집합 · ㎡당 운영 문턱(대체용)은 그 집합의 최대 단가."""
    measures = _load("measure_cost_catalog.json")["default"]["measures"]
    by_scope = {k for k, m in measures.items() if m["work_scope"] == "operational"}
    by_class = {k for k, m in measures.items() if m["measure_class"] == "operational"}
    assert by_scope == by_class and by_scope
    assert _declared()["investment_tiers"]["value"]["operational_max_krw_per_m2"] == \
        max(float(measures[k]["capex_krw_per_m2"]) for k in by_scope)
    # 외피 공사 = 대공사 — 단 카탈로그가 스스로 '저비용 처치'라고 적은 기밀(SEAL)은 제한된 범위
    passive = {k: m["work_scope"] for k, m in measures.items() if m["measure_class"] == "passive"}
    assert all(s == "major_project" for k, s in passive.items() if "저비용" not in measures[k].get("note", "")), passive
    assert all(s == "minor_repair" for k, s in passive.items() if "저비용" in measures[k].get("note", "")), passive
