# -*- coding: utf-8 -*-
"""0.3.74 (2026-10-01) — 게이트웨이 3회전 묶음이 기다리는 EC 행(캠페인 scratch/capability_first/EC_ROWS_NEEDED_round3.md · requests_round1.md WP2 §4).

① 요청 값 그대로(근거가 선 값만 — 근거 없는 M01 끄는 시각 서명은 넣지 않았다) ② 0.3.73 태그와 잎 전부 대조(문구 포함 — 판 표지와
원형 별칭 목록 뒤 붙이기만 예외) ③ 어휘 적재 검사의 새 칸(요금 종별 · 설정 동작 · 적용 전제 · 쉬운 이름 · 용도→원형 관계 · 계절 체계)이
막아야 할 것을 막고 통과시킬 것을 통과시킨다 ④ 새 행·칸이 생성본에 닿는다 ⑤ 넣지 않은 요청이 행으로 새지 않았다. 검사가 돈 건수를 단언한다.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))

import gen_constants as gc  # noqa: E402
import vocabulary_gate as vg  # noqa: E402

_spec = importlib.util.spec_from_file_location("_t0372", Path(__file__).with_name("test_declared_assumptions_0372.py"))
_t0372 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_t0372)
strict_additive, _at_tag = _t0372.strict_additive, _t0372._at_tag

NEW_ROWS_0374 = ("operation_reading_window", "operation_reading_freshness", "cohort_city_min_share")
CHANGED_SCHEMAS = ("building_usage_map.json", "building_archetypes.json", "target_vocabulary.json", "ems_strategies.json",
                   "declared_assumptions.json")
#: 원형 별칭 목록 셋은 **뒤에 붙이기만** 했다(아래에서 앞 원소를 따로 본다) — 그 밖은 판 표지뿐
ALIAS_PATHS = {f"building_archetypes.json:/default/doe_buildings/{c}/aliases" for c in ("B01", "B02", "B03")}
ALLOWED_CHANGES = {"/version", "/updated", "/$comment", *ALIAS_PATHS,
                   # 2026-10-01 125b530: M00 한국어 이름을 쉬운 말로(사람 대면 이름표만)
                   "ems_strategies.json:/default/strategies/M00/name_kr"}


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


# ── ① 요청 값 그대로 ──────────────────────────────────────────────────────────────────────────────────────────
def test_requested_values_are_there_with_their_basis():
    checked = 0
    um, ba, tv, ems, d = (_load(n)["default"] for n in CHANGED_SCHEMAS)
    # E6-1 (가) 용도 별칭 · (나) 원형 별칭(DOE 규모 구간의 어휘 결정)
    assert um["usage_archetype"]["usage_aliases"]["사무실"] == "업무시설"; checked += 1
    docs = ba["doe_buildings"]
    assert docs["B01"]["aliases"][-3:] == ["큰 사무실", "대형 사무실", "큰 오피스"]; checked += 1
    assert docs["B02"]["aliases"][-1:] == ["중형 사무실"]; checked += 1
    assert docs["B03"]["aliases"][-3:] == ["작은 사무실", "소형 사무실", "작은 오피스"]; checked += 1
    # E6-2 원형 전기 종별 — 주택 = 주택용 · 학교 = 교육용 · 나머지 = 일반용
    cls = {c: m["electricity_price_class"] for c, m in docs.items()}
    assert {c for c, v in cls.items() if v == "residential"} == {"B16", "B17", "B18"}; checked += 1
    assert {c for c, v in cls.items() if v == "education_2024"} == {"B07", "B08"}; checked += 1
    assert {c for c, v in cls.items() if v == "general"} == set(docs) - {"B16", "B17", "B18", "B07", "B08"} and len(docs) == 18; checked += 1
    assert "E6-2" in ba["electricity_price_class_rule"]["basis"]; checked += 1
    # E6-3 가스 종별 — 가정 = 주택용(81.4) · 공장 = 산업용(95.6) · 건물·점포·포트폴리오 = null(참조 단가 그대로)
    kinds = tv["air_asset_kinds"]
    assert {k: v["gas_price_class"] for k, v in kinds.items()} == {"BLD": None, "FAC": "industrial", "HOM": "residential", "RET": None,
                                                                  "PRT": None}; checked += 1
    market = _load("market_prices.json")["default"]
    gas = {k: vg._walk(market, v["market_prices_ref"]) for k, v in tv["gas_price_classes"].items() if isinstance(v, dict)}
    assert gas == {"residential": 81.4, "industrial": 95.6}; checked += 1
    assert market["unit_prices"]["gas_krw"] == 80.0 and market["unit_prices"]["residential"]["gas_krw"] == 45.0; checked += 1  # 참조·동결 값 그대로
    # E4-1 설정 동작(단일만) · E5-1 적용 전제 · WP2 §4 쉬운 이름
    st = ems["strategies"]
    assert {c: m["setpoint_action"] for c, m in st.items() if m.get("setpoint_action") not in (None, "none")} == {
        "M00": "fixed_with_night_setback", "M04": "comfort_band_dynamic", "M05": "comfort_band_dynamic", "M09": "pre_peak_shift",
        "M10": "peak_hour_setup", "M16": "night_setback"}; checked += 1
    assert all("setpoint_action" not in m for m in st.values() if m["type"] == "combined"); checked += 1
    assert "PHYSICS_SPEC_2026-09-15_CONTRACT" in ems["setpoint_actions"]["basis"] and "M10" in ems["setpoint_actions"]["basis"]; checked += 1
    assert {c: m["applies_when"] for c, m in st.items() if "applies_when" in m} == {
        "M00": ["non_operating_hours"], "M01": ["daily_start_stop"], "M03": ["multiple_plant_units"], "M06": ["non_operating_hours"],
        "M08": ["mechanical_outdoor_air"], "M16": ["non_operating_hours"], "M18": ["ess_installed"]}; checked += 1
    assert st["M12"]["easy_name_kr"] == ("조합: 켜고 끄는 시각 맞추기 + 바깥 공기로 식히기 + 냉동기·보일러 필요한 대수만 돌리기 + "
                                         "쾌적 범위 안 설정온도 자동 조절(엄격)"); checked += 1
    assert all(m.get("easy_name_kr") for m in st.values()) and len(st) == 23; checked += 1
    # E5-1 편의점 24시간(선언 가정) · R3F-3 관계
    cs = um["usages"]["convenience_store"]
    assert cs["operates_24h"] is True and cs["operates_24h_basis"]["classification"] == "assumed" and "OCCUPIED_HOURS" in cs["operates_24h_basis"]["basis"]; checked += 1
    rows = um["usage_archetype"]["rows"]
    assert rows["편의점"]["archetype_relation"] == rows["교육연구시설"]["archetype_relation"] == "nearest_other_type"; checked += 1
    assert rows["업무시설"]["archetype_relation"] == rows["공동주택"]["archetype_relation"] == "same_type"; checked += 1
    assert "archetype_relation" not in rows["방송통신시설"]; checked += 1
    # E5-2 · E5-3 · R3F-1 · R3F-2
    assert d["serving_display_limits"]["value"]["display_significant_digits"] == 3; checked += 1
    assert d["operation_reading_window"]["value"] == {"load_shape_window_days": 28, "load_shape_min_days": 7, "portfolio_reading_sample": 12}; checked += 1
    assert d["operation_reading_freshness"]["value"] == {"max_season_lag": 0, "season_system_ref": "calendar_conventions.question_season_system"}; checked += 1
    assert (d["cohort_city_min_share"]["value"], d["cohort_city_min_share"]["comparison"]) == (0.5, "greater_than"); checked += 1
    # WP2 §4 시나리오 한글 이름 — 열쇠 순서 = 시뮬 축
    axes = ba["sim_axes"]
    assert list(axes["scenario_names"]) == axes["scenarios"] and all(v["name_kr"] for v in axes["scenario_names"].values()); checked += 1
    assert checked == 26


def test_new_rows_have_the_row_shape():
    units = set(_load("interface_types.json")["$defs"]["QuantityUnit"]["enum"])
    d = _load("declared_assumptions.json")["default"]
    problems = [p for k in NEW_ROWS_0374 for p in _t0372.row_problems(k, d[k], units)]
    assert problems == [] and all(k in d for k in NEW_ROWS_0374)
    # 근거 없는 값은 '선언' 이라고 스스로 적는다
    assert all("선언" in d[k]["basis"] for k in NEW_ROWS_0374 if d[k]["basis_kind"] == "declared_demo_assumption")


# ── ② 0.3.73 태그와 잎 전부 ────────────────────────────────────────────────────────────────────────────────────
def test_additive_against_the_0373_tag():
    checked = 0
    for name in CHANGED_SCHEMAS:
        old = _at_tag("v0.3.73", name)
        if old is None:
            pytest.skip(f"[해당 없음] git 태그 v0.3.73 을 못 읽었다({name}) — 통과가 아니다(못 잼)")
        problems, n = strict_additive(old, _load(name), "", ALLOWED_CHANGES, name)
        assert not problems, problems
        checked += n
    old_docs = _at_tag("v0.3.73", "building_archetypes.json")["default"]["doe_buildings"]
    new_docs = _load("building_archetypes.json")["default"]["doe_buildings"]
    for code in ("B01", "B02", "B03"):
        before = old_docs[code]["aliases"]
        assert new_docs[code]["aliases"][:len(before)] == before, code       # 뒤에 붙이기만
    assert checked >= 2500, checked                     # 다섯 파일의 잎 전부(실측 2,582 — 0 건이면 그것이 사고다)


# ── ③ 어휘 적재 검사 ───────────────────────────────────────────────────────────────────────────────────────────
def _mutations():
    """(이름, 문서 고치기, 결함 문장에 있어야 할 글자) — 막아야 할 것."""
    S = lambda docs: docs["ems_strategies"]["default"]  # noqa: E731
    return [
        ("archetype price class unknown", lambda d: d["building_archetypes"]["default"]["doe_buildings"]["B16"].update(electricity_price_class="home"), "home"),
        ("one archetype without a class", lambda d: d["building_archetypes"]["default"]["doe_buildings"]["B04"].pop("electricity_price_class"), "B04"),
        ("gas class unknown", lambda d: d["target_vocabulary"]["default"]["air_asset_kinds"]["HOM"].update(gas_price_class="house"), "house"),
        ("gas class slot missing on a kind", lambda d: d["target_vocabulary"]["default"]["air_asset_kinds"]["BLD"].pop("gas_price_class"), "BLD"),
        ("gas class ref not a number", lambda d: d["target_vocabulary"]["default"]["gas_price_classes"]["industrial"].update(
            market_prices_ref="retail_reference_2026.gas_retail_seoul"), "industrial"),
        ("setpoint action unknown", lambda d: S(d)["strategies"]["M04"].update(setpoint_action="pmv_band"), "pmv_band"),
        ("single strategy without an action", lambda d: S(d)["strategies"]["M07"].pop("setpoint_action"), "M07"),
        ("combined strategy with an action", lambda d: S(d)["strategies"]["M12"].update(setpoint_action="comfort_band_dynamic"), "M12"),
        ("applies_when unknown condition", lambda d: S(d)["strategies"]["M18"].update(applies_when=["battery"]), "battery"),
        ("condition decided by an undeclared fact", lambda d: S(d)["applicability_conditions"]["values"]["non_operating_hours"].update(
            decided_by_usage_fact="closes_at_night"), "closes_at_night"),
        ("combined easy name hand-written", lambda d: S(d)["strategies"]["M11"].update(easy_name_kr="통합 운전"), "M11"),
        ("easy name on two strategies", lambda d: S(d)["strategies"]["M05"].update(easy_name_kr=S(d)["strategies"]["M04"]["easy_name_kr"]), "M04"),
        ("relation unknown", lambda d: d["building_usage_map"]["default"]["usage_archetype"]["rows"]["편의점"].update(archetype_relation="same"), "same"),
        ("relation missing on a row with an archetype", lambda d: d["building_usage_map"]["default"]["usage_archetype"]["rows"]["공장"].pop(
            "archetype_relation"), "공장"),
        ("relation on a row without an archetype", lambda d: d["building_usage_map"]["default"]["usage_archetype"]["rows"]["방송통신시설"].update(
            archetype_relation="nearest_other_type"), "방송통신시설"),
        ("freshness points at no season system", lambda d: d["declared_assumptions"]["default"]["operation_reading_freshness"]["value"].update(
            season_system_ref="calendar_conventions.lunar_system"), "lunar_system"),
        ("freshness lag negative", lambda d: d["declared_assumptions"]["default"]["operation_reading_freshness"]["value"].update(max_season_lag=-1),
         "max_season_lag"),
    ]


def test_vocabulary_gate_passes_with_the_new_checks():
    docs = vg._load_dir(SCHEMAS)
    problems, checks = vg.problems(docs)
    assert problems == [] and checks >= 450, (problems, checks)
    new_problems, new_checks = vg._problems_0374(lambda n: (docs.get(n) or {}).get("default") or {}, docs.get("building_usage_map"))
    assert new_problems == [] and new_checks >= 120, (new_problems, new_checks)     # 0 건이면 그것이 사고다


def test_vocabulary_gate_blocks_what_it_must_0374():
    base = vg._load_dir(SCHEMAS)
    blocked = 0
    for name, mutate, needle in _mutations():
        docs = copy.deepcopy(base)
        mutate(docs)
        problems, checks = vg.problems(docs)
        assert checks > 0 and any(needle in p for p in problems), (name, problems)
        blocked += 1
    assert blocked == len(_mutations()) == 17


def test_vocabulary_gate_lets_through_what_it_must_0374():
    """막으면 안 되는 것: 적용 전제가 없는 전략(칸 없음) · 가르는 사실이 없는 전제(설비 — 못 잼) · 가스 종별 null(참조 단가) ·
    계절 종별(needs_month)의 수 표 · 칸을 아직 쓰지 않은 옛 문서(0.3.73 모양 — 새 검사는 칸이 있을 때만 돈다)."""
    base = vg._load_dir(SCHEMAS)
    passed = 0
    old = {name: _at_tag("v0.3.73", f"{name}.json") for name in ("building_usage_map", "building_archetypes", "target_vocabulary",
                                                               "ems_strategies", "declared_assumptions")}
    mutations = [lambda d: d["ems_strategies"]["default"]["strategies"]["M08"].pop("applies_when"),
                 lambda d: d["ems_strategies"]["default"]["strategies"]["M02"].update(applies_when=["mechanical_outdoor_air"]),
                 lambda d: d["target_vocabulary"]["default"]["air_asset_kinds"]["FAC"].update(gas_price_class=None),
                 lambda d: d["target_vocabulary"]["default"]["electricity_price_classes"]["general_low_voltage"].update(needs_month=True)]
    if all(old.values()):
        mutations.append(lambda d: d.update(old))
    for mutate in mutations:
        docs = copy.deepcopy(base)
        mutate(docs)
        problems, checks = vg.problems(docs)
        assert problems == [] and checks > 0, problems
        passed += 1
    assert passed == len(mutations) >= 4


# ── ④ 생성본 도달 ──────────────────────────────────────────────────────────────────────────────────────────────
def test_new_rows_reach_the_generated_constants():
    schemas = gc.load_schemas()
    full = gc.gen_python(schemas)
    ns: dict = {}
    exec(full, ns)
    assert all(k in ns["DECLARED_ASSUMPTIONS"] for k in NEW_ROWS_0374)
    assert ns["STRATEGIES"]["M04"]["setpoint_action"] == "comfort_band_dynamic" and ns["STRATEGIES"]["M01"]["applies_when"] == ["daily_start_stop"]
    assert ns["USAGE_ARCHETYPE"]["usage_aliases"]["사무실"] == "업무시설" and "archetype_relations" in ns["USAGE_ARCHETYPE"]
    assert ns["AIR_ASSET_KINDS"]["HOM"]["gas_price_class"] == "residential"
    assert ns["AXIS_ALIAS_INDEX"]["archetype"][ns["ec_axis_key"]("큰 사무실")] == "B01"
    assert ns["AXIS_ALIAS_INDEX"]["archetype"][ns["ec_axis_key"]("작은오피스")] == "B03"
    # 용도 별칭 '사무실' = 업무시설 규칙 — 면적 모름이면 중형 + 면적 미확인(새 원형을 짓지 않는다) · 면적이 크면 대형
    r = ns["ec_usage_to_archetype"]("사무실", None, ns["USAGE_ARCHETYPE"])
    assert (r["archetype"], r["flag"]) == ("B02", "area_unverified")
    assert ns["ec_usage_to_archetype"]("사무실", 20000, ns["USAGE_ARCHETYPE"])["archetype"] == "B01"
    usages = ns["BUILDING_USAGES"]
    assert usages["convenience_store"]["operates_24h"] is True and usages["office"]["archetype_code"] == "B02"
    checked = 0
    for project in ("8sim-shared", "building-energy-3d", "airos-energy-decision"):
        got: dict = {}
        exec(gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS[project]), got)
        assert all(k in got["DECLARED_ASSUMPTIONS"] for k in NEW_ROWS_0374), project
        checked += 1
    assert checked == 3


def test_generated_models_accept_the_new_fields():
    from pydantic import ValidationError
    from energy_contracts._pydantic_models import building_usage_map, ems_strategies, target_vocabulary
    entry = _load("target_vocabulary.json")["default"]["air_asset_kinds"]["HOM"]
    assert target_vocabulary.AirAssetKindEntry.model_validate(entry).gas_price_class == "residential"
    with pytest.raises(ValidationError):                                   # 막는 쪽: 모르는 칸은 여전히 거절(additionalProperties false)
        target_vocabulary.AirAssetKindEntry.model_validate({**entry, "water_price_class": "x"})
    row = _load("building_usage_map.json")["default"]["usage_archetype"]["rows"]["편의점"]
    assert building_usage_map.UsageArchetypeRow.model_validate(row).root.archetype_relation.value == "nearest_other_type"
    with pytest.raises(ValidationError):                                   # 막는 쪽: 어휘 밖 관계
        building_usage_map.UsageArchetypeRow.model_validate({**row, "archetype_relation": "same"})
    source = Path(ems_strategies.__file__).read_text(encoding="utf-8")
    assert all(name in source for name in ("easy_name_kr", "setpoint_action", "applies_when"))


# ── ⑤ 넣지 않은 요청 ───────────────────────────────────────────────────────────────────────────────────────────
def test_declined_requests_did_not_become_rows():
    """근거 없는 새 문턱은 넣지 않았다 — M01 끄는(정지) 시각 서명(R3F-4: 새 수이고 인용할 근거가 없다). 효과 결함 설비(R3F-5 · H_D)와 설비 라벨(E4-2)은
    시뮬 세션·사용자 결정 몫이라 칸이 없다."""
    st = _load("ems_strategies.json")["default"]["strategies"]
    assert st["M01"]["observable_signature"]["metric"] == "weekday_ramp_hour"
    assert "weekday_rampdown_hour" not in json.dumps(st)
    docs = _load("building_archetypes.json")["default"]["doe_buildings"]
    assert all("hvac_effect_defects" not in m for m in docs.values())
