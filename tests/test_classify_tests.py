"""classify_tests._strip_headerless_pytestmark unit tests (TD-9).

H1 회귀 패턴 ("canonical 위 + raw 아래") 등 4 케이스 검증.
SSOT: scripts/classify_tests.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from classify_tests import (  # noqa: E402
    _MARKER_BLOCK_HEAD,
    _MARKER_BLOCK_TAIL,
    _strip_headerless_pytestmark,
)

pytestmark = [pytest.mark.tier("T2"), pytest.mark.group("G7"), pytest.mark.stage("S2")]


CANONICAL_BLOCK = (
    f"{_MARKER_BLOCK_HEAD}\n"
    "import pytest as _ssot_pytest\n"
    "pytestmark = [\n"
    "    _ssot_pytest.mark.tier('T2'),\n"
    "    _ssot_pytest.mark.group('G7'),\n"
    "    _ssot_pytest.mark.stage('S2'),\n"
    "]\n"
    f"{_MARKER_BLOCK_TAIL}\n"
)

RAW_PYTESTMARK = (
    "import pytest as _ssot_pytest\n"
    "pytestmark = [\n"
    "    _ssot_pytest.mark.tier('T2'),\n"
    "    _ssot_pytest.mark.group('G7'),\n"
    "    _ssot_pytest.mark.stage('S2'),\n"
    "]\n"
)


def test_canonical_only_preserved():
    """sentinel 으로 감싼 canonical block 은 보존."""
    src = f'"""module doc."""\n\n{CANONICAL_BLOCK}\n\ndef test_x(): pass\n'
    out = _strip_headerless_pytestmark(src)
    assert out == src, "canonical 블록이 변형되었음"
    assert _MARKER_BLOCK_HEAD in out
    assert "pytestmark = [" in out


def test_raw_only_stripped():
    """sentinel 없는 raw pytestmark + dangling import 는 함께 제거."""
    src = f'"""module doc."""\n\n{RAW_PYTESTMARK}\n\ndef test_x(): pass\n'
    out = _strip_headerless_pytestmark(src)
    assert "pytestmark = [" not in out, "raw pytestmark 가 남아 있음"
    assert "import pytest as _ssot_pytest" not in out, "dangling import 가 남아 있음"
    assert "def test_x(): pass" in out


def test_canonical_above_raw_below_H1_regression():
    """H1 회귀: canonical 위 + raw 아래. canonical 보존, raw 만 제거."""
    src = (
        '"""module doc."""\n'
        "\n"
        f"{CANONICAL_BLOCK}"
        "\n"
        "# 사용자가 실수로 추가한 raw pytestmark\n"
        f"{RAW_PYTESTMARK}"
        "\n"
        "def test_x(): pass\n"
    )
    out = _strip_headerless_pytestmark(src)
    assert _MARKER_BLOCK_HEAD in out, "canonical sentinel 이 제거됨"
    assert _MARKER_BLOCK_TAIL in out, "canonical tail 이 제거됨"
    # canonical 내부에 pytestmark = [ 가 1번만 남아야 함
    assert out.count("pytestmark = [") == 1, (
        f"raw 가 안 지워졌거나 canonical 까지 삭제됨 (count={out.count('pytestmark = [')})"
    )
    assert "# 사용자가 실수로 추가한 raw pytestmark" in out


def test_raw_with_dangling_import_stripped_together():
    """raw pytestmark 직전 라인이 'import pytest as _ssot_pytest' 면 함께 제거."""
    src = (
        '"""module doc."""\n'
        "\n"
        "import os\n"
        "import pytest as _ssot_pytest\n"
        "pytestmark = [_ssot_pytest.mark.tier('T2')]\n"
        "\n"
        "def test_x(): pass\n"
    )
    out = _strip_headerless_pytestmark(src)
    assert "pytestmark = [" not in out
    assert "import pytest as _ssot_pytest" not in out, "dangling alias import 가 남음"
    assert "import os" in out, "관련 없는 import 가 함께 삭제됨"
    assert "def test_x(): pass" in out
