"""패키지 버전 단일 SSOT 가드 (사냥꾼 라운드 M13, 2026-06-08).

이전엔 pyproject.toml(0.3.3) ≠ __init__.__version__(0.2.3) ≠ CLAUDE.md 표(0.2.0)
3중 drift → wheel 메타데이터와 런타임 __version__ 불일치. 본 테스트가 pyproject 와
__version__ 동기를 강제한다.
"""
from __future__ import annotations

import pathlib

import energy_contracts

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_version_matches_pyproject() -> None:
    assert energy_contracts.__version__ == _pyproject_version(), (
        f"__version__({energy_contracts.__version__}) != "
        f"pyproject({_pyproject_version()}) — 단일 SSOT 동기 필요"
    )
