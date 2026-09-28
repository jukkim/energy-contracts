"""일반화 G0·G1 (2026-09-28) — 정본 한 곳 + 투영이 맞는가. 검사마다 양쪽 반례(막을 것을 막나 / 막지 말 것을 통과시키나).

검증기 규칙: 검사가 실제로 돌았는지(0건 아님)까지 본다. 같은 규칙이 두 곳이면 같은 원문인지 바이트로 본다.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import gen_constants as gc  # noqa: E402
import validate_ssot as vs  # noqa: E402
from energy_contracts import axes, identifiers  # noqa: E402
from energy_contracts import rules_pure as rp  # noqa: E402


@pytest.fixture()
def tmp_schemas(tmp_path: Path) -> Path:
    d = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, d)
    return d


def _edit(d: Path, name: str, fn) -> None:
    fp = d / name
    data = json.loads(fp.read_text(encoding="utf-8"))
    fn(data)
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── G0: 전략 목록 한 곳 ─────────────────────────────────────────────────────────

def test_strategy_list_is_one_list_projected_twice():
    want, have = gc.strategy_list_targets()
    assert len(want) == 23 and want[0] == "M00" and want[-1] == "M22"
    assert all(v == want for v in have.values()), have
    assert vs.check_strategy_list_projection() == []


def test_strategy_projection_catches_and_repairs_a_stale_enum(tmp_schemas: Path):
    _edit(tmp_schemas, "common.json", lambda d: d["$defs"]["Strategy"].__setitem__("enum", [f"M{i:02d}" for i in range(21)]))
    assert vs.check_strategy_list_projection(tmp_schemas), "21종으로 되돌린 common 을 못 잡았다"
    assert gc.sync_strategy_projection(check_only=True, schemas_dir=tmp_schemas) == ["common.json#/$defs/Strategy/enum"]
    gc.sync_strategy_projection(check_only=False, schemas_dir=tmp_schemas)
    assert vs.check_strategy_list_projection(tmp_schemas) == []


def test_b18_is_an_archetype_with_kbep_id_17():
    docs = json.loads((SCHEMAS / "building_archetypes.json").read_text(encoding="utf-8"))["default"]["doe_buildings"]
    assert docs["B18"]["name_en"] == "DetachedHouse" and docs["B18"]["kbep_id"] == 17
    assert [docs[c]["kbep_id"] for c in sorted(docs)] == list(range(18))


def test_replay_policy_source_hash_matches_source_and_stale_hash_is_caught(tmp_schemas: Path):
    src = json.loads((SCHEMAS / "airos_replay_anomaly_policy.json").read_text(encoding="utf-8"))["default"]["source"]
    if not (vs.WORKSPACE_ROOT / src["path"]).exists():
        pytest.skip("원천이 이 작업공간에 없다 — 못 잼")
    assert vs.check_replay_policy_source() == []
    _edit(tmp_schemas, "airos_replay_anomaly_policy.json",
          lambda d: d["default"]["source"].__setitem__("sha256", "682d4091a9ffef2133531080bac9a0bdaeba49ccb8613d0402ce80b87622a4e5"))
    assert vs.check_replay_policy_source(tmp_schemas), "옛 해시를 못 잡았다"


# ── G1: 용도 → 원형 한 표 (결정 D1) ─────────────────────────────────────────────

@pytest.mark.parametrize("area,want,flag", [
    (511, "B03", None), (2322.576, "B03", None), (2322.6, "B02", None), (4982, "B02", None),
    (13935.456, "B02", None), (13935.5, "B01", None), (46320, "B01", None),
    (None, "B02", "area_unverified"), (0, "B02", "area_unverified"), ("n/a", "B02", "area_unverified"),
])
def test_office_by_gross_floor_area(area, want, flag):
    r = axes.usage_to_archetype("업무시설", area)
    assert (r["archetype"], r["flag"], r["absence"]) == (want, flag, None)


def test_usage_without_row_has_no_archetype_not_a_default():
    assert axes.usage_to_archetype("종교시설")["absence"] == "usage_not_in_archetype_table"
    assert axes.usage_to_archetype("종교시설")["archetype"] is None
    assert axes.usage_to_archetype("")["absence"] == "usage_unknown"
    assert axes.usage_to_archetype(None)["archetype"] is None
    assert axes.usage_to_archetype("단독주택")["archetype"] == "B18"
    assert axes.usage_to_archetype("아파트")["archetype"] == "B16"   # 용도 별칭


def test_usage_projections_agree_and_a_divergent_copy_is_caught(tmp_schemas: Path):
    assert vs.check_usage_archetype() == []
    _edit(tmp_schemas, "building_archetypes.json",
          lambda d: d["default"]["usage_to_buildwise"].__setitem__("업무시설", "large_office"))
    assert any("업무시설" in v for v in vs.check_usage_archetype(tmp_schemas))


def test_usage_band_gap_is_caught(tmp_schemas: Path):
    def gap(d):
        d["default"]["usage_archetype"]["office_by_gross_floor_area"]["bands"][1]["min_m2_exclusive"] = 3000.0
    _edit(tmp_schemas, "building_usage_map.json", gap)
    assert any("이어지지 않는다" in v for v in vs.check_usage_archetype(tmp_schemas))


def test_usages_archetype_names_follow_the_table(tmp_schemas: Path):
    _edit(tmp_schemas, "building_usage_map.json",
          lambda d: d["default"]["usages"]["residential_house"].__setitem__("archetype", "SmallHotel"))
    assert any("residential_house" in v for v in vs.check_usage_archetype(tmp_schemas))


# ── G1: 축 어휘 ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kind,tok,code", [
    ("city", "서울특별시", "C01"), ("city", "Seoul", "C01"), ("city", 17, "C18"), ("city", "목포시", "C18"),
    ("archetype", "LO", "B01"), ("archetype", "MidriseApartment", "B16"), ("archetype", "midrise_apt", "B16"),
    ("archetype", "B18", "B18"), ("archetype", "단독주택", "B18"),
    ("hvac", "HA", "H_A"), ("hvac", "g", "H_G"), ("hvac", 3, "H_D"),
    ("strategy", 5, "M05"), ("strategy", "m22", "M22"),
])
def test_axis_encode_accepts_every_declared_form(kind, tok, code):
    assert axes.encode(kind, tok) == code


@pytest.mark.parametrize("kind,tok", [("city", "Tokyo"), ("city", "광주시"), ("archetype", "School"),
                                      ("archetype", "Retail"), ("hvac", "H_H"), ("strategy", "M99"), ("city", None)])
def test_axis_encode_refuses_unknown_tokens_by_name(kind, tok):
    with pytest.raises(KeyError, match="AXIS_TOKEN_UNKNOWN"):
        axes.encode(kind, tok)


def test_kbep_ids_and_fast_path():
    assert axes.kbep_id("archetype", "B18") == 17
    assert axes.kbep_id("strategy", "M15") == 15
    with pytest.raises(KeyError, match="KBEP_FAST_PATH_OUT"):
        axes.kbep_id("strategy", "M16")


def test_generator_and_package_build_the_same_alias_index():
    built = gc.axis_tables(gc.load_schemas())
    assert built["index"] == axes.alias_index()
    assert sum(len(v) for v in built["index"].values()) > 100


def test_alias_collision_is_refused_not_resolved():
    docs = {"B01": {"name_en": "LargeOffice", "kbep_id": 0, "aliases": ["X"]},
            "B02": {"name_en": "MediumOffice", "kbep_id": 1, "aliases": ["x"]}}
    with pytest.raises(ValueError, match="충돌"):
        rp.ec_axis_tables(docs, {}, {}, {}, [])
    assert vs.check_axis_tables() == []


# ── G1: 호환표 정본 행 ─────────────────────────────────────────────────────────

def test_hvac_compat_has_every_canonical_code_and_strategy(tmp_schemas: Path):
    compat = gc.hvac_ems_compat(gc.load_schemas())
    assert sorted(compat) == [f"H_{c}" for c in "ABCDEFG"]
    assert all(len(row) == 23 for row in compat.values())
    assert compat["H_D"]["M01"] == "compatible" and compat["H_C"]["M02"] == "infeasible"
    assert vs.check_hvac_canonical_rows() == []
    _edit(tmp_schemas, "hvac_ems_matrix.json", lambda d: d["default"]["canonical_rows"].__setitem__("H_D", "D"))
    assert any("H_D" in v for v in vs.check_hvac_canonical_rows(tmp_schemas))


# ── G1: 식별자 · 승계 ──────────────────────────────────────────────────────────

def test_identifier_patterns_both_sides():
    assert identifiers.matches("AirAssetId", "AIR-RET-1234") and identifiers.matches("AirAssetId", "AIR-HOM-001")
    assert not identifiers.matches("AirAssetId", "AIR-PRT-001") and not identifiers.matches("AirAssetId", "AIR-BLD-01")
    assert identifiers.matches("BuildingMgmtNo", "1" * 25) and not identifiers.matches("BuildingMgmtNo", "1" * 19)
    assert identifiers.matches("ParcelId", "1" * 19) and not identifiers.matches("ParcelId", "1" * 25)
    with pytest.raises(KeyError):
        identifiers.pattern("NoSuchId")


def test_building_on_parcel_uses_succession_and_all_19_digits():
    no = "4211010100100150001" + "000123"
    assert identifiers.parcel_of_building(no) == "5111010100100150001"
    assert identifiers.building_on_parcel(no, "5111010100100150001")
    assert identifiers.building_on_parcel(no, "4211010100100150001")
    # 다른 시군구의 같은 [5:19] — 옛 게이트웨이 판정은 통과시켰다
    assert not identifiers.building_on_parcel(no, "5113010100100150001")
    assert not identifiers.building_on_parcel("12345", "5111010100100150001")


def test_region_code_succession_rules():
    assert identifiers.current_region_code("42") == "51"
    assert identifiers.current_region_code("42720") == "51720"
    assert identifiers.current_region_code("45113") == "52113"
    assert identifiers.current_region_code("41195") == "41192"
    assert identifiers.current_region_code("47720") == "27720"
    assert identifiers.current_region_code("43710") == "43710"          # split — 동 없이 추측하지 않는다
    assert identifiers.current_region_code("11110") == "11110"
    assert identifiers.current_region_code("4211") is None


def test_admin_succession_check_both_sides(tmp_schemas: Path):
    assert vs.check_admin_succession() == []
    _edit(tmp_schemas, "region_codes.json",
          lambda d: d["default"]["admin_succession"]["sigungu_successor"].__setitem__("41192", "41190"))
    assert any("다시 승계" in v for v in vs.check_admin_succession(tmp_schemas))


# ── 순수 규칙 원문 한 벌 — 생성본에 바이트 그대로 ─────────────────────────────────

def _defs(text: str) -> dict[str, str]:
    import ast
    return {n.name: ast.dump(n) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}


def test_generated_files_carry_the_pure_rules_verbatim():
    """생성본의 규칙 함수 = rules_pure 원문(AST 동일). 소비처 필터가 빈 줄만 줄이므로 AST 로 견준다."""
    src = gc.rules_pure_source()
    want = _defs(src)
    assert len(want) >= 6
    full = gc.gen_python(gc.load_schemas())
    assert src.rstrip("\n") in full
    for proj in ("building-energy-3d", "8sim-shared", "agentleague"):
        filtered = gc.apply_exports_filter(full, "python", gc.PROJECT_TARGETS[proj])
        got = _defs(filtered)
        assert {k: got.get(k) for k in want} == want, proj
        ns: dict = {}
        exec(filtered, ns)
        assert ns["ec_usage_to_archetype"]("업무시설", 30000)["archetype"] == "B01"
        if "AXIS_ALIAS_INDEX" in ns:
            assert ns["ec_axis_encode"]("city", "부산광역시") == "C02"
        else:   # 표를 내보내지 않은 생성본에서는 이름 있는 실패(빈 표로 조용히 통과하지 않는다)
            with pytest.raises(LookupError):
                ns["ec_axis_encode"]("city", "부산광역시")


def test_percentile_and_carbon_rules():
    assert rp.ec_percentile([], 0.5) is None and rp.ec_percentile([None], 0.5) is None
    assert rp.ec_percentile([1, 2, 3, 4], 0.5) == 2.5 and rp.ec_percentile([5], 0.9) == 5.0
    with pytest.raises(ValueError):
        rp.ec_percentile([1, 2], 50)
    assert axes.carbon_kg({"electricity": 1000}) == pytest.approx(417.3)
    with pytest.raises(KeyError, match="CARBON_FUEL_UNKNOWN"):
        axes.carbon_kg({"coal": 1})


# ── G1 2차: 달력 · 문턱 · 계절 TOU · 할인율 ─────────────────────────────────────

def test_calendar_thresholds_tariff_pass_and_divergent_summer_rate_is_caught(tmp_schemas: Path):
    assert vs.check_calendar_thresholds_tariff() == []
    _edit(tmp_schemas, "market_prices.json",
          lambda d: d["default"]["electricity_tariff"].__setitem__("peak", 999.0))
    assert any("대표 TOU" in v for v in vs.check_calendar_thresholds_tariff(tmp_schemas))


def test_season_system_must_cover_each_month_once(tmp_schemas: Path):
    _edit(tmp_schemas, "calendar_conventions.json",
          lambda d: d["default"]["season_systems"]["kepco_tariff"]["seasons"].__setitem__("summer", [6, 7, 8, 9]))
    assert any("kepco_tariff" in v for v in vs.check_calendar_thresholds_tariff(tmp_schemas))


def test_discount_rate_is_d3_with_a_source(tmp_schemas: Path):
    full = gc.gen_python(gc.load_schemas())
    ns: dict = {}
    exec(full, ns)
    assert ns["DISCOUNT_RATE_DEFAULT"] == 0.045 and "4.5%" in ns["DISCOUNT_RATE_SOURCE"]["basis"]
    assert ns["JUDGEMENT_THRESHOLDS"]["data_quality"]["eui_plausible_kwh_m2"]["max"] == 3000.0
    assert ns["CALENDAR_CONVENTIONS"]["season_systems"]["kepco_tariff"]["seasons"]["summer"] == [6, 7, 8]
    _edit(tmp_schemas, "measure_cost_catalog.json",
          lambda d: d["default"]["method"].pop("discount_rate_source"))
    assert any("할인율" in v or "discount" in v for v in vs.check_calendar_thresholds_tariff(tmp_schemas))
