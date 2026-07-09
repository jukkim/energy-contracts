#!/usr/bin/env python
"""verify_mcode_boundary — M-code 네임스페이스 경계 재발방지 가드 (Hunter 5-Stage ④).

배경(2026-07-10): EMS 전략 코드의 상한이 정규식 `^M(0[0-9]|1[0-9]|20)$` 형태로
소스 스키마 13곳 + 생성기 2곳 + 문서에 하드코딩·복제돼 있었다. 코드 추가마다 ~15곳을
손대야 해서 매번 절반이 누락 → 영구 drift(M17=LightingControl vs PV vs PMV+DC 3진영).

Phase 1(2026-07-10)에서 경계를 M99로 미래안전화(유효성=enum)했다. 이 가드는 그 상태가
다시 하드코딩으로 퇴행하지 않도록, 그리고 stale 사본이 canonical로 오인되지 않도록 지킨다.

검사:
  1. 소스 스키마/생성기에 구 경계 하드코딩(`1[0-9]|20)` 형태) 재출현 금지 (설명문 이력 제외).
  2. control_command enum ⊇ ems_strategies enum (pin-lockstep 불변식 선제 검사).
  3. legacy_ems_code_mapping.valid_count == ems_strategies enum 길이.
  4. stale 원시 스키마 사본(build/·venv/) 의 enum 이 canonical 과 다르면 경고(오인 방지).

exit 0 = 통과 / 1 = 위반.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "energy_contracts" / "schemas"

# 구 경계 하드코딩 시그니처 (M20 상한). 설명문에 이력으로 남기는 것은 허용 리스트로 예외.
OLD_BOUNDARY = re.compile(r"1\[0-9\]\|20\)")
# 소스만 검사 (생성물·빌드·venv·캐시·scratch 제외)
SOURCE_GLOBS = ["energy_contracts/schemas/*.json", "scripts/gen_constants.py",
                "scripts/validate_ssot.py", ".spectral.yaml", "protocols/*.yaml"]
# 이력 서술이 허용된 위치 (파일:이유)
HISTORY_ALLOW = {
    "energy_contracts/schemas/common.json",  # description 에 "구 → M99" 이력 서술
}


def _iter_source_files():
    seen = set()
    for g in SOURCE_GLOBS:
        for p in ROOT.glob(g):
            if p.is_file() and p not in seen:
                seen.add(p)
                yield p


def check_no_hardcoded_boundary() -> list[str]:
    v = []
    for p in _iter_source_files():
        rel = p.relative_to(ROOT).as_posix()
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for ln, line in enumerate(txt.splitlines(), 1):
            if OLD_BOUNDARY.search(line):
                # 이력 서술 허용: description/주석 라인 + 허용 파일
                if rel in HISTORY_ALLOW and ("description" in line or "#" in line):
                    continue
                v.append(f"구 경계 하드코딩 재출현: {rel}:{ln} — `1[0-9]|20)` "
                         f"(M99 형태 `[2-9][0-9]` 사용, 유효성=enum)")
    return v


def check_control_command_superset() -> list[str]:
    ems = json.loads((SCHEMAS / "ems_strategies.json").read_text(encoding="utf-8"))
    cc = json.loads((SCHEMAS / "control_command.json").read_text(encoding="utf-8"))
    ems_codes = set(ems["$defs"]["StrategyCode"]["enum"])
    cc_codes = set(re.findall(r'"(M\d\d)"', json.dumps(cc)))
    missing = sorted(ems_codes - cc_codes)
    if missing:
        return [f"control_command enum 이 ems_strategies enum 의 부분집합 아님 — 누락 {missing} "
                f"(pin-lockstep 위반 예정: 릴리스 전 control_command.json 에 추가 필요)"]
    return []


def check_valid_count() -> list[str]:
    ems = json.loads((SCHEMAS / "ems_strategies.json").read_text(encoding="utf-8"))
    legacy = json.loads((SCHEMAS / "legacy_ems_code_mapping.json").read_text(encoding="utf-8"))
    n = len(ems["$defs"]["StrategyCode"]["enum"])
    vc = legacy["properties"]["ssot"]["properties"]["valid_count"]["const"]
    if n != vc:
        return [f"valid_count({vc}) != enum 길이({n}) — legacy_ems_code_mapping.json 갱신 필요"]
    return []


def check_stale_copies() -> list[str]:
    """build/·venv 원시 사본이 canonical enum 과 다르면 경고(오인 방지). 부재 = OK."""
    warns = []
    canonical = set(json.loads((SCHEMAS / "ems_strategies.json")
                               .read_text(encoding="utf-8"))["$defs"]["StrategyCode"]["enum"])
    for cand in ROOT.glob("build/**/ems_strategies.json"):
        try:
            e = set(json.loads(cand.read_text(encoding="utf-8"))["$defs"]["StrategyCode"]["enum"])
        except Exception:
            continue
        if e != canonical:
            warns.append(f"stale 사본 발견(오인 위험): {cand.relative_to(ROOT).as_posix()} "
                         f"— enum {sorted(e - canonical) or sorted(canonical - e)} 불일치. "
                         f"`python -m build` 재빌드 또는 삭제.")
    return warns


def main() -> int:
    violations, warnings = [], []
    violations += check_no_hardcoded_boundary()
    violations += check_control_command_superset()
    violations += check_valid_count()
    warnings += check_stale_copies()

    for w in warnings:
        print(f"[mcode-boundary] WARN: {w}")
    if violations:
        print(f"\n[mcode-boundary] 위반 {len(violations)}건:")
        for x in violations:
            print(f"  - {x}")
        return 1
    print("[mcode-boundary] OK — 경계 하드코딩 없음, enum 불변식 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
