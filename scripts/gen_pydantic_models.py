"""26 SSOT 스키마 → Pydantic v2 BaseModel 일괄 생성 (Phase L-2).

datamodel-code-generator 기반.
- 자체 gen_constants.py 는 'dict 형태 상수' 생성 (런타임 import).
- 본 스크립트는 추가로 'Pydantic v2 모델' 생성 (validation + type safety).

사용:
  pip install datamodel-code-generator[ruff]
  python scripts/gen_pydantic_models.py --all
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "energy_contracts" / "schemas"
OUT_DIR = ROOT / "energy_contracts" / "_pydantic_models"


def gen_one(schema_fp: Path) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{schema_fp.stem}.py"
    cmd = [
        "datamodel-codegen",
        "--input", str(schema_fp),
        "--output", str(out),
        "--input-file-type", "jsonschema",
        "--output-model-type", "pydantic_v2.BaseModel",
        "--use-default",
        "--use-schema-description",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[FAIL] {schema_fp.name}: {r.stderr.strip()[:200]}")
        return 1
    print(f"[OK]   {schema_fp.name} → _pydantic_models/{out.name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="26 schema 전체 생성")
    ap.add_argument("--schema", help="단일 schema 파일명 (예: run_modes.json)")
    args = ap.parse_args()

    if args.schema:
        fp = SCHEMAS_DIR / args.schema
        if not fp.exists():
            print(f"미존재: {fp}")
            return 2
        return gen_one(fp)

    if args.all:
        fails = 0
        for fp in sorted(SCHEMAS_DIR.glob("*.json")):
            fails += gen_one(fp)
        return fails

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
