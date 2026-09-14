"""이름 정본 게이트가 **빨간불을 낼 수 있는가** (2026-09-15).

E→M 표 두 벌을 대조하던 옛 검사는 없는 경로를 읽어 **한 번도 비교하지 않았다**.
초록만 본 게이트는 게이트가 아니다 — 여기서는 스키마 사본을 일부러 깨서 각 검사가
위반을 내는지, 원본에서는 0 건인지 둘 다 확인한다.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import legacy_e_codes  # noqa: E402
import validate_ssot  # noqa: E402

SCHEMAS = ROOT / "energy_contracts" / "schemas"


@pytest.fixture()
def schemas(tmp_path: Path) -> Path:
    dst = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, dst)
    return dst


def _edit(schemas_dir: Path, name: str, fn) -> None:
    p = schemas_dir / name
    d = json.loads(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 원본은 초록 ──────────────────────────────────────────────────────────────

def test_canonical_schemas_are_green():
    assert validate_ssot.check_legacy_code_consistency() == []
    assert validate_ssot.check_hvac_display_names() == []


def test_projection_matches_canonical():
    ems = json.loads((SCHEMAS / "ems_strategies.json").read_text(encoding="utf-8"))
    assert ems["default"]["legacy_mapping"]["gcs_e_codes"] == legacy_e_codes.gcs_projection()


# ── 두 표가 갈라지면 빨강 ────────────────────────────────────────────────────

def test_red_when_projection_diverges(schemas: Path):
    _edit(schemas, "ems_strategies.json",
          lambda d: d["default"]["legacy_mapping"]["gcs_e_codes"].__setitem__("E6", "M04"))
    v = validate_ssot.check_legacy_code_consistency(schemas)
    assert any("gcs_e_codes[E6]" in x for x in v), v


def test_red_when_projection_misses_a_code(schemas: Path):
    """옛 검사가 놓친 모양 — 한쪽에만 있는 코드(E5·E12·E13 누락)."""
    _edit(schemas, "ems_strategies.json",
          lambda d: d["default"]["legacy_mapping"]["gcs_e_codes"].pop("E13"))
    v = validate_ssot.check_legacy_code_consistency(schemas)
    assert any("gcs_e_codes[E13]" in x for x in v), v


def test_red_when_canonical_path_is_unreadable(schemas: Path):
    """정본을 못 읽으면 '비교할 것 없음' 이 아니라 위반이다."""
    _edit(schemas, "legacy_ems_code_mapping.json",
          lambda d: d["properties"].pop("deprecated_e_codes"))
    v = validate_ssot.check_legacy_code_consistency(schemas)
    assert v and "로드 실패" in v[0], v


def test_red_when_maps_to_breaks_the_rule(schemas: Path):
    def brk(d):
        node = d["properties"]["deprecated_e_codes"]["properties"]["E5"]
        node["maps_to"] = "M10"   # 2026-09-15 이전 오기(생성기 번호 뜻)
    _edit(schemas, "legacy_ems_code_mapping.json", brk)
    v = validate_ssot.check_legacy_code_consistency(schemas)
    assert any("deprecated_e_codes[E5].maps_to" in x for x in v), v


def test_maps_to_rule_examples():
    atoms = legacy_e_codes.atomic_sets()
    assert legacy_e_codes.expected_maps_to(["M07"], atoms) == ("M07", True)
    assert legacy_e_codes.expected_maps_to(["M02", "M03"], atoms) == ("M11", False)
    assert legacy_e_codes.expected_maps_to(["M06", "M02"], atoms) == ("M14", False)


# ── 파이프라인이 내보내는 E-code 가 정본에 없으면 빨강 ─────────────────────────

def _fake_workspace(tmp_path: Path, labels: list[str], mapping: dict) -> Path:
    import yaml
    ws = tmp_path / "ws"
    spec = ws / "8.simulation" / "reverse" / "configs" / "data_spec.yaml"
    spec.parent.mkdir(parents=True)
    spec.write_text(yaml.safe_dump({"ems": {"e_labels": labels, "e_to_m": mapping}}), encoding="utf-8")
    return ws


def test_emitter_green_when_mirror_matches(tmp_path: Path):
    table = legacy_e_codes.canonical_e_codes()
    labels = ["E0", "E5", "E6", "E8", "E10"]
    ws = _fake_workspace(tmp_path, labels, {c: table[c]["components"] for c in labels})
    assert validate_ssot.check_e_code_emitter_coverage(workspace_root=ws) == []


def test_red_when_emitter_sends_unmapped_code(tmp_path: Path):
    ws = _fake_workspace(tmp_path, ["E0", "E14"], {"E0": ["M00"], "E14": ["M02"]})
    v = validate_ssot.check_e_code_emitter_coverage(workspace_root=ws)
    assert any("E14" in x for x in v), v


def test_red_when_emitter_mirror_drifts(tmp_path: Path):
    ws = _fake_workspace(tmp_path, ["E6"], {"E6": ["M04"]})
    v = validate_ssot.check_e_code_emitter_coverage(workspace_root=ws)
    assert any("E6" in x and "components" in x for x in v), v


def test_emitter_absent_is_not_counted_as_pass(tmp_path: Path, capsys):
    assert validate_ssot.check_e_code_emitter_coverage(workspace_root=tmp_path / "empty") == []
    assert "UNMEASURED" in capsys.readouterr().out


# ── 공조 방식 이름 ───────────────────────────────────────────────────────────

def test_red_when_hvac_name_missing(schemas: Path):
    _edit(schemas, "region_codes.json",
          lambda d: d["default"]["hvac_types"]["H_B"].__setitem__("name_kr", ""))
    v = validate_ssot.check_hvac_display_names(schemas)
    assert any("H_B" in x and "name_kr" in x for x in v), v


def test_red_when_alias_points_to_two_codes(schemas: Path):
    _edit(schemas, "region_codes.json",
          lambda d: d["default"]["hvac_types"]["H_C"]["aliases"].append("B"))
    v = validate_ssot.check_hvac_display_names(schemas)
    assert any("'B'" in x for x in v), v


def test_red_when_matrix_row_points_elsewhere(schemas: Path):
    _edit(schemas, "hvac_ems_matrix.json",
          lambda d: d["properties"]["hvac_types"]["properties"]["HG"].__setitem__("const", "H_E"))
    v = validate_ssot.check_hvac_display_names(schemas)
    assert any("'HG'" in x for x in v), v


def test_every_serving_alias_has_a_name():
    """서빙 인코더(kbep_client._HVAC_TYPE_TO_ID)가 받는 21 표기 전부 이름이 붙는다."""
    region = json.loads((SCHEMAS / "region_codes.json").read_text(encoding="utf-8"))
    names = {}
    for code, meta in region["default"]["hvac_types"].items():
        for alias in [code, *meta["aliases"]]:
            names[alias] = meta["name_kr"]
    for letter in "ABCDEFG":
        for form in (letter, f"H{letter}", f"H_{letter}"):
            assert names.get(form), form


# ── pre-commit 은 파일 하나를 루트로 넘긴다 — 그때도 파일 이름 면제가 먹는가 ─────────

def test_precommit_file_root_keeps_filename_exemption():
    """`ems_strategies.json` 은 SSOT 자체라 구 코드 표(ems_simulation M0~M8)가 정당하다.

    2026-09-15 전: 스테이징된 파일을 루트로 넘기면 면제 키가 `"/."` 가 되어 9건으로 막혔다.
    """
    assert validate_ssot.scan_legacy_strategies([SCHEMAS / "ems_strategies.json"]) == []
