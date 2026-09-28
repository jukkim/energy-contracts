"""2026-09-28 최종 라운드 — 용도 표 한 벌(X2) · 분류 어휘 1.3(②) · 선언 가정 상수(N32).

⛔ 이 파일은 만든 라운드에 돌리지 않았다(전역 ⭐⭐⭐⭐ 3단계). 묶음 끝 §4 에서 한 번.
반례는 양쪽을 건다 — 막아야 할 것을 막나 · 막으면 안 될 것을 통과시키나. 검사 건수를 단언해 빈 집합 통과를 막는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"
sys.path.insert(0, str(ROOT / "scripts"))

from energy_contracts import axes  # noqa: E402
from energy_contracts import rules_pure as rp  # noqa: E402
import gen_constants as gc  # noqa: E402
import validate_ssot as vs  # noqa: E402


def _vocab() -> dict:
    return json.loads((SCHEMAS / "data_classification.json").read_text(encoding="utf-8"))["default"]["classification"]


# ── X2 용도 표 한 벌 ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("floors,want", [(None, "B16"), (1, "B16"), (5, "B16"), (6, "B17"), (20, "B17"), (0, "B16")])
def test_apartment_by_floors(floors, want):
    r = axes.usage_to_archetype("공동주택", None, floors)
    assert r["archetype"] == want and r["absence"] is None


def test_twenty_floor_apartment_is_not_an_office():
    assert axes.usage_to_archetype("아파트", None, 20)["archetype"] == "B17"


def test_convenience_store_is_b11_and_registry_usage_stays_b03():
    assert axes.usage_to_archetype("편의점")["archetype"] == "B11"
    assert axes.usage_to_archetype("제1종근린생활시설")["archetype"] == "B03"


def test_datacenter_is_named_absence_not_a_guess():
    r = axes.usage_to_archetype("데이터센터")
    assert r["archetype"] is None and r["absence"] == "no_doe_archetype"
    assert axes.usage_to_archetype("종교시설")["absence"] == "usage_not_in_archetype_table"


def test_generated_building_usages_derive_archetype_from_rows():
    schemas = gc.load_schemas()
    bu = gc.building_usages_resolved(schemas)
    assert len(bu) >= 10, "파생 0건은 통과가 아니다"
    assert bu["convenience_store"]["archetype_code"] == "B11"
    assert bu["convenience_store"]["archetype"] == "QuickServiceRestaurant"
    assert bu["office"]["archetype_code"] == "B02"                  # 면적 미상 = 중형(기존 값)
    assert bu["other"]["archetype"] is None and bu["other"]["archetype_absence"]


def test_hand_written_usage_archetype_is_caught(tmp_path: Path):
    for p in SCHEMAS.glob("*.json"):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    assert vs.check_usage_archetype(tmp_path) == []
    fp = tmp_path / "building_usage_map.json"
    d = json.loads(fp.read_text(encoding="utf-8"))
    d["default"]["usages"]["office"]["archetype"] = "LargeOffice"
    fp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert any("office" in v for v in vs.check_usage_archetype(tmp_path))


# ── ② 분류 어휘 ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("words,want", [
    (["measured"], "measured"),
    (["measured", "virtual"], "mixed"),
    (["measured", "measured_with_imputed"], "measured_with_imputed"),
    (["measured", "imputed"], "measured_with_imputed"),
    (["virtual", "synthetic"], "virtual"),
    (["measured", None], "unknown"),
    ([], "unknown"),
    (["measured_with_virtual_assumptions"], "mixed"),
    (["whatever_word"], "unknown"),
])
def test_combine(words, want):
    assert rp.ec_classification_combine(words, _vocab()) == want


def test_every_word_has_a_display_class_in_the_enum():
    d = json.loads((SCHEMAS / "data_classification.json").read_text(encoding="utf-8"))
    display = set(d["$defs"]["EvidenceDisplayClass"]["enum"])
    words = d["default"]["classification"]["words"]
    assert set(words) == set(d["$defs"]["ClassificationWord"]["enum"])
    assert len(words) >= 17
    for w, row in words.items():
        assert row["display_class"] in display, w
        assert row["source"] is None or row["source"] in d["$defs"]["DataSource"]["enum"], w
    for alias, target in d["default"]["classification"]["aliases"].items():
        assert target in words, alias


def test_missing_is_never_measured():
    assert rp.ec_classification_normalize(None, _vocab()) == "unknown"
    assert rp.ec_classification_normalize("", _vocab()) == "unknown"


# ── N32 선언 가정 상수 ─────────────────────────────────────────────────────────

def test_declared_assumptions_have_class_and_source():
    d = json.loads((SCHEMAS / "declared_assumptions.json").read_text(encoding="utf-8"))["default"]
    checked = 0
    for name, node in d.items():
        items = node.values() if name in ("hazard_days", "complaint_temperature") else [node]
        for it in items:
            assert it.get("classification") in ("declared", "assumed"), name
            assert it.get("source"), name
            checked += 1
    assert checked >= 9
    assert abs(sum(d["end_use_split_default"]["shares"].values()) - 1.0) < 1e-9
