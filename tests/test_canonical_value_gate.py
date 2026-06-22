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
