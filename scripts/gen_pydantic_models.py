"""SSOT 스키마 전체 → Pydantic v2 BaseModel 일괄 생성 (Phase L-2).

datamodel-code-generator 기반.
- 자체 gen_constants.py 는 'dict 형태 상수' 생성 (런타임 import).
- 본 스크립트는 추가로 'Pydantic v2 모델' 생성 (validation + type safety).
- cross-file $ref (예: agent_contracts → data_classification) 는 자동으로
  로컬 $defs 에 인라인 후 datamodel-codegen 호출. (Phase D 준비, 2026-05-19)

사용:
  pip install datamodel-code-generator[ruff]
  python scripts/gen_pydantic_models.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "energy_contracts" / "schemas"
OUT_DIR = ROOT / "energy_contracts" / "_pydantic_models"


def _safe_defname(existing: set[str], path_part: str, fragment_tail: str) -> str:
    base = fragment_tail or Path(path_part).stem
    base = re.sub(r"[^A-Za-z0-9_]", "_", base)
    if base not in existing:
        return base
    stem = re.sub(r"[^A-Za-z0-9_]", "_", Path(path_part).stem)
    candidate = f"{stem}__{base}"
    i = 2
    while candidate in existing:
        candidate = f"{stem}__{base}_{i}"
        i += 1
    return candidate


def _resolve_external_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """schema 내 cross-file $ref 를 로컬 $defs 에 인라인 후 ref 재작성."""
    schema = json.loads(json.dumps(schema))
    schema.setdefault("$defs", {})
    cache: dict[tuple[str, str], str] = {}

    def resolve_ref(ref: str) -> str:
        if "#" in ref:
            path_part, fragment = ref.split("#", 1)
        else:
            path_part, fragment = ref, ""
        if (path_part, fragment) in cache:
            return cache[(path_part, fragment)]
        target_fp = SCHEMAS_DIR / Path(path_part).name
        if not target_fp.exists():
            raise FileNotFoundError(f"cross-ref target missing: {target_fp}")
        target = json.loads(target_fp.read_text(encoding="utf-8"))
        node: Any = target
        if fragment:
            for part in fragment.strip("/").split("/"):
                node = node[part]
        fragment_tail = fragment.rstrip("/").split("/")[-1] if fragment else ""
        defname = _safe_defname(set(schema["$defs"].keys()), path_part, fragment_tail)
        schema["$defs"][defname] = node
        new_ref = f"#/$defs/{defname}"
        # cache 를 먼저 등록(순환 ref 방어) 후, 인라인된 node 의 transitive 외부 ref 를
        # 그 자리에서 재해소한다. 사냥꾼 라운드 M7 (2026-06-08): 기존엔 walk 가 $defs 를
        # 순회한 뒤 properties 처리 중 추가된 $def 내부의 외부 ref 가 미해소로 남아,
        # 2 단계 cross-file ref 도입 시 datamodel-codegen 입력에 외부 $ref 가 새어 FAIL 했다.
        cache[(path_part, fragment)] = new_ref
        walk(node)
        return new_ref

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#"):
                node["$ref"] = resolve_ref(ref)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)
    return schema


def gen_one(schema_fp: Path) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{schema_fp.stem}.py"
    schema = json.loads(schema_fp.read_text(encoding="utf-8"))
    has_external = False

    def _scan(node: Any) -> None:
        nonlocal has_external
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and not ref.startswith("#"):
                has_external = True
            for v in node.values():
                _scan(v)
        elif isinstance(node, list):
            for v in node:
                _scan(v)

    _scan(schema)

    if has_external:
        resolved = _resolve_external_refs(schema)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(resolved, tmp, ensure_ascii=False)
            input_fp = Path(tmp.name)
    else:
        input_fp = schema_fp

    cmd = [
        "datamodel-codegen",
        "--input", str(input_fp),
        "--output", str(out),
        "--input-file-type", "jsonschema",
        "--output-model-type", "pydantic_v2.BaseModel",
        "--use-default",
        "--use-schema-description",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        # 사냥꾼 라운드 LOW (2026-06-08): datamodel-codegen 미설치 시 traceback 대신 안내.
        print("[ERROR] datamodel-codegen 미설치 — "
              "`pip install datamodel-code-generator[ruff]` 후 재시도")
        return 2
    finally:
        if has_external:
            try:
                input_fp.unlink()
            except OSError:
                pass
    if r.returncode != 0:
        print(f"[FAIL] {schema_fp.name}: {r.stderr.strip()[:200]}")
        return 1
    note = " (cross-ref inlined)" if has_external else ""
    print(f"[OK]   {schema_fp.name} → _pydantic_models/{out.name}{note}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="schemas/*.json 전체 생성")
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
        # 사냥꾼 라운드 LOW (2026-06-08): exit code 정규화 (실패 건수 누적 대신 0/1).
        return 1 if fails else 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
