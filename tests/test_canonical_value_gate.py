"""scan_stale_canonical_values unit tests — 폐기 canonical 수치(구값) 잔재 게이트.

EC 스키마를 단일 root 로 강제하기 위한 구값 탐지기.
- active 코드 라인의 구값(0.4594 등)은 잡는다
- 변경 이력 서술 라인(이전/구값/→)은 면제
- 현행 정본값(0.4173)은 잡지 않는다
- 숫자 경계: 0.459 가 0.4591 안에서 오탐되지 않는다
SSOT: scripts/validate_ssot.py

본 파일은 fixture 로 구값(0.4594 등)을 포함하므로 게이트 자기참조를 면제한다:
SSOT_ALLOW_STALE_CANONICAL
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from validate_ssot import (  # noqa: E402
    STALE_CANONICAL_VALUES,
    scan_stale_canonical_values,
)

pytestmark = [pytest.mark.tier("T2"), pytest.mark.group("G7"), pytest.mark.stage("S2")]


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_catches_active_stale_value(tmp_path):
    _write(tmp_path, "bad.py", "CARBON_FACTOR = 0.4594\n")
    v = scan_stale_canonical_values([tmp_path])
    assert any(p.name == "bad.py" for p, _, _ in v)


def test_exempts_history_note(tmp_path):
    # 변경 이력을 적는 라인은 구값이 있어도 면제
    _write(tmp_path, "hist.py", "CARBON = 0.4173  # 이전 0.4594 폐기\n")
    v = scan_stale_canonical_values([tmp_path])
    assert not any(p.name == "hist.py" for p, _, _ in v)


def test_does_not_flag_current_value(tmp_path):
    _write(tmp_path, "ok.py", "CARBON = 0.4173\nPE = 0.728\n")
    v = scan_stale_canonical_values([tmp_path])
    assert not any(p.name == "ok.py" for p, _, _ in v)


def test_numeric_boundary_no_substring_match(tmp_path):
    # '0.459' 매니페스트가 '0.4591'(별도 구값) 안에서 이중 매칭되지 않아야
    _write(tmp_path, "b.py", "X = 0.4591\n")
    v = [t for t in scan_stale_canonical_values([tmp_path]) if t[0].name == "b.py"]
    # 0.4591 자체는 구값이므로 1건만(0.459 substring 으로 추가 매칭 금지)
    assert len(v) == 1


def test_comment_line_skipped(tmp_path):
    _write(tmp_path, "c.py", "# legacy ref 0.4594 kept for docs\nY = 1\n")
    v = scan_stale_canonical_values([tmp_path])
    assert not any(p.name == "c.py" for p, _, _ in v)


def test_manifest_nonempty_and_well_formed():
    assert STALE_CANONICAL_VALUES
    for row in STALE_CANONICAL_VALUES:
        assert len(row) == 3  # (구값, 현행값, 설명)
        stale, current, _desc = row
        assert stale != current


# --- equipment_taxonomy.point_sets (v1.1.0, 2026-08-01) -----------------------

def test_point_set_mnemonics_share_the_cpa_point_vocabulary():
    """point_sets 의 니모닉은 **CPA `{point}` 세그먼트와 같은 어휘**여야 한다.

    여기서 새 니모닉을 발명하면 주소 어휘가 둘로 갈린다 — 같은 급기온도를 어떤
    소비단은 SAT 로, 어떤 소비단은 DAT 로 부르게 된다.
    """
    import json
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas"
    tax = json.loads((root / "equipment_taxonomy.json").read_text(encoding="utf-8"))
    tele = json.loads((root / "telemetry.json").read_text(encoding="utf-8"))

    # CPA 마지막 세그먼트({point})의 형식 = 대문자 니모닉
    cpa = tele["$defs"]["CanonicalPointAddress"]["pattern"]
    point_seg = re.search(r"\\.\(?\[A-Z\]\[A-Z0-9_\]\*\)?\$$", cpa)
    assert point_seg, f"CPA 패턴에서 point 세그먼트를 못 찾았다: {cpa}"

    kinds = set(tax["$defs"]["EquipmentKind"]["enum"])
    sets = tax["default"]["point_sets"]
    assert set(sets) <= kinds, f"EquipmentKind 밖의 설비: {sorted(set(sets) - kinds)}"

    roles = set(tax["$defs"]["PointRole"]["enum"])
    for kind, points in sets.items():
        assert points, f"{kind}: 빈 점 집합"
        seen = set()
        for p in points:
            m = p["mnemonic"]
            assert re.fullmatch(r"[A-Z][A-Z0-9_]*", m), f"{kind}.{m}: CPA 니모닉 형식 아님"
            assert m not in seen, f"{kind}: 니모닉 중복 {m}"
            seen.add(m)
            assert p["role"] in roles, f"{kind}.{m}: 미지원 role {p['role']}"
            if "brick" in p:
                assert p["brick"].startswith("brick:"), f"{kind}.{m}: brick 형식"


def test_point_sets_declare_their_standard_sources():
    """표준을 근거로 댔다면 **출처를 남긴다** — 근거 없는 표준을 만들지 않기 위해서다."""
    import json
    from pathlib import Path

    tax = json.loads((Path(__file__).resolve().parents[1] / "energy_contracts"
                      / "schemas" / "equipment_taxonomy.json").read_text(encoding="utf-8"))
    src = tax["default"]["point_sets_sources"]
    for key in ("haystack", "brick", "ashrae_g36"):
        assert key in src and src[key], f"출처 누락: {key}"


def test_required_points_exist_for_the_equipment_mgcc_draws():
    """MGCC 관제도가 그리는 설비 6종에 **기대 점이 정의돼 있어야** 한다."""
    import json
    from pathlib import Path

    tax = json.loads((Path(__file__).resolve().parents[1] / "energy_contracts"
                      / "schemas" / "equipment_taxonomy.json").read_text(encoding="utf-8"))
    sets = tax["default"]["point_sets"]
    for kind in ("ahu", "chiller", "boiler", "fan", "lighting", "ess"):
        assert kind in sets, f"MGCC 가 그리는 설비인데 점 집합이 없다: {kind}"
        assert any(p.get("required") for p in sets[kind]), \
            f"{kind}: 기대(required) 점이 하나도 없다 — 커버리지 판정이 불가능하다"
