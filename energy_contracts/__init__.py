"""energy-contracts — VW/GB/EA/Agents 공유 인터페이스 SSOT.

Phase C (a12): wheel 배포로 모든 consumer repo 가 동일 git SHA pin.
- schemas/: JSON Schema SSOT (35+ 파일)
- _pydantic_models/: schemas 로부터 자동 생성된 Pydantic 모델
"""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

__version__ = "0.2.3"

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
