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
# ⚠ **버전 문자열은 한 곳에서만 온다.** 예전엔 여기와 `pyproject.toml` 두 곳에
#   손으로 적었고, 그래서 또 어긋났다(2026-08-21: pyproject 0.3.42 인데 여기 0.3.40).
#   손으로 맞추는 두 곳은 결국 갈라진다 — 설치 메타데이터에서 **파생**시킨다.
#   ⚠ 설치 안 된 작업 트리에서는 metadata 가 없다. 그때는 pyproject 를 직접 읽는다
#     (조용히 "0.0.0" 으로 두면 그 값이 시험을 통과시켜 버린다).
#   ⚠ **순서가 중요하다.** 작업 트리에 `pyproject.toml` 이 있으면 그게 정본이다 —
#     editable 설치의 메타데이터는 설치 시점에 굳어 낡는다(실측: pyproject 0.3.42
#     인데 metadata 0.3.40). 설치된 wheel 에는 pyproject 가 없으므로 metadata 로 간다.
def _resolve_version() -> str:
    try:
        import re as _re
        from pathlib import Path as _P
        t = (_P(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8")
        m = _re.search(r'^version\s*=\s*"([^"]+)"', t, _re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    try:
        from importlib.metadata import version as _v
        return _v("energy-contracts")
    except Exception:
        pass
    raise RuntimeError(
        "energy-contracts 버전을 못 읽었다 — 설치 메타데이터도 pyproject 도 없다. "
        "여기서 임의값을 돌려주면 '설치된 것 == 핀' 검사가 거짓으로 통과한다.")


__version__ = _resolve_version()

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
