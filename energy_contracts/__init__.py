"""energy-contracts — VW/GB/EA/Agents 공유 인터페이스 SSOT.

Phase C (a12): wheel 배포로 모든 consumer repo 가 동일 git SHA pin.
- schemas/: JSON Schema SSOT (현재 수는 list_schemas() 로 확인)
- _pydantic_models/: schemas 로부터 자동 생성된 Pydantic 모델
"""
from __future__ import annotations

import json
from pathlib import Path

# 사냥꾼 라운드 M13 (2026-06-08): pyproject.toml 의 version 과 일치 (단일 SSOT).
#   이전엔 __init__ 0.2.3 ≠ pyproject 0.3.3 로 wheel 메타 ≠ 런타임 __version__ 불일치.
#   tests/test_version_consistency.py 가 pyproject 와 동기 가드.
__version__ = "0.3.14"

# 패키지 내부 schemas 디렉토리 위치 — wheel 설치 후에도 작동.
SCHEMAS_DIR: Path = Path(__file__).parent / "schemas"


def load_schema(name: str) -> dict:
    """schemas/{name}.json 을 dict 로 로드.

    Example:
        >>> from energy_contracts import load_schema
        >>> run_modes = load_schema("run_modes")
        >>> run_modes["$id"]
    """
    fname = name if name.endswith(".json") else f"{name}.json"
    return json.loads((SCHEMAS_DIR / fname).read_text(encoding="utf-8"))


def list_schemas() -> list[str]:
    """schemas 디렉토리의 모든 *.json 이름 (확장자 제외)."""
    return sorted(p.stem for p in SCHEMAS_DIR.glob("*.json"))


__all__ = ["__version__", "SCHEMAS_DIR", "load_schema", "list_schemas"]
