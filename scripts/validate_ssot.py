"""SSOT 위반 검사기 — pre-commit / CI 용도.

검사 항목:
  1. 하드코딩된 구 전략 코드 (M0, M1, ..., M8 단독) 탐지
  2. 포트 할당 충돌 (port_allocation.json 기준)
  3. JSON Schema 일관성 (common.json $defs 와 다른 스키마 정합)
  4. _generated_constants.* SOURCE_HASH drift (Phase H 추가)
  5. port_range 슬롯과 단일 port 항목의 잠복 충돌 (Phase H 추가)

사용법:
  python validate_ssot.py [--check strategy|ports|schemas|generated|all] [paths...]
  python validate_ssot.py --check all  # 기본
  python validate_ssot.py --check strategy ../edge-agent/src
  python validate_ssot.py --pre-commit  # 변경된 파일만 검사

종료 코드:
  0 — 통과 / 1 — 위반 발견 / 2 — 검사 자체 오류
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = CONTRACTS_ROOT / "schemas"
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]  # myjob/

# ── 1. 전략 코드 ─────────────────────────────────────────────────────────────

# 구 코드(M0~M8) 패턴 — string literal 안에서만 매칭하여 false positive 최소화
# "M5", 'M5' 형태 (식별자 P3-M2 등은 제외)
LEGACY_STRATEGY_RE = re.compile(r"""['"](M[0-8])['"]""")

# 파일 레벨 면제 마커
FILE_EXEMPT_MARKERS = (
    "SSOT_ALLOW_LEGACY_STRATEGY",  # 의도된 negative test 파일
    "AUTO-GENERATED",              # gen_constants.py 산출물
)

# 예외 허용 경로 — 마이그레이션 주석/문서/CHANGELOG 등
STRATEGY_EXEMPT_PATTERNS = [
    "AUDIT-",       # 감사 보고서 (마이그레이션 기록)
    "CHANGELOG",
    "MIGRATION",
    "REVIEW",
    "/reviews/",
    "validate_ssot.py",
    "SSOT_GOVERNANCE",
    "ems_strategies.json",  # SSOT 자체
    "/scratch/",            # 임시 작업 공간
]

# 검사 대상 확장자
STRATEGY_SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".html", ".yaml", ".yml"}


def scan_legacy_strategies(paths: list[Path]) -> list[tuple[Path, int, str]]:
    violations = []
    for root in paths:
        if root.is_file():
            files = [root]
        else:
            files = [p for p in root.rglob("*") if p.is_file()
                     and p.suffix in STRATEGY_SCAN_EXTS]
        for fp in files:
            s = str(fp).replace("\\", "/")
            if any(pat in s for pat in STRATEGY_EXEMPT_PATTERNS):
                continue
            # 라이브러리/빌드 산출물 스킵
            if any(part in fp.parts for part in
                   ("node_modules", "dist", ".git", ".venv", "venv", "env",
                    "__pycache__", "build", "site-packages", ".next", "out")):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # 파일 레벨 면제 마커
            if any(marker in text for marker in FILE_EXEMPT_MARKERS):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                # 주석 라인 건너뜀 (마이그레이션 메모 허용)
                stripped = line.lstrip()
                if stripped.startswith(("#", "//", "*", "<!--")):
                    continue
                # 라인 후미 주석 안의 노트 (어디든 invalid/legacy 키워드) 면제
                if re.search(r"#.*\b(old|legacy|negative|rejected|invalid)\b",
                             line, re.I):
                    continue
                if re.search(r"//.*\b(old|legacy|negative|rejected|invalid)\b",
                             line, re.I):
                    continue
                if LEGACY_STRATEGY_RE.search(line):
                    violations.append((fp, lineno, line.strip()[:120]))
    return violations


# ── 2. 포트 충돌 ─────────────────────────────────────────────────────────────

def load_port_allocation() -> dict:
    fp = SCHEMAS_DIR / "port_allocation.json"
    if not fp.exists():
        return {}
    return json.loads(fp.read_text(encoding="utf-8"))


def check_port_conflicts() -> list[str]:
    """동일 포트에 둘 이상의 deployed 서비스 매핑 시 위반.

    Phase H: port_range 슬롯이 단일 port 항목과 겹치는지 잠복 검사.
    """
    data = load_port_allocation()
    if not data:
        return ["port_allocation.json 미존재"]
    seen: dict[int, list[str]] = defaultdict(list)
    ranges: list[tuple[int, int, str, str]] = []  # (lo, hi, name, status)
    for svc in data.get("services", []):
        port = svc.get("port")
        port_range = svc.get("port_range")
        if port_range:
            # "8011-8016" 형태
            try:
                lo_s, hi_s = port_range.split("-")
                ranges.append((int(lo_s), int(hi_s),
                               svc.get("name", "?"), svc.get("status", "?")))
            except ValueError:
                pass
            continue
        if svc.get("status") != "deployed":
            continue
        if port is None:
            continue
        # machine_override로 blocked인 항목은 충돌에서 제외
        if svc.get("machine_override", {}).get("A") == "blocked (Docker)":
            continue
        seen[port].append(svc.get("name", "?"))
    violations = []
    for port, names in seen.items():
        if len(names) > 1:
            violations.append(f"포트 {port} 중복: {', '.join(names)}")
    # port_range 잠복 충돌 (deployed 단일 port와 겹침)
    for lo, hi, rng_name, rng_status in ranges:
        for port, names in seen.items():
            if lo <= port <= hi:
                # multi-mode dormant 는 잠복 표시만 (warning, not failure)
                if rng_status == "multi-mode":
                    continue
                violations.append(
                    f"포트 {port} ({names[0]}) 가 range {lo}-{hi} ({rng_name}, {rng_status}) 와 충돌")
    return violations


# ── 4. _generated_constants.* SOURCE_HASH drift (Phase H) ──────────────────

GENERATED_TARGETS: list[tuple[str, str]] = [
    ("python", "projects/edge-agent/src/_generated_constants.py"),
    ("python", "projects/gridbridge/src/_generated_constants.py"),
    ("python", "projects/building-energy-3d/src/shared/_generated_constants.py"),
    ("ts",     "projects/building-energy-3d/frontend/src/shared/_generated_constants.ts"),
    ("python", "projects/agentleague/backend/_generated_constants.py"),
    ("python", "projects/eduarena/backend/_generated_constants.py"),
]


def check_generated_drift() -> list[str]:
    """_generated_constants.* 파일의 SOURCE_HASH 헤더 vs 실 schemas hash 비교.

    수동 편집된 파일을 탐지한다. gen_constants.py와 동일 알고리즘.
    """
    violations: list[str] = []
    try:
        import importlib.util
        gen_path = CONTRACTS_ROOT / "scripts" / "gen_constants.py"
        spec = importlib.util.spec_from_file_location("gen_constants", gen_path)
        if spec is None or spec.loader is None:
            return ["gen_constants.py 로드 실패"]
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        schemas = gen.load_schemas()
        expected_hash = gen.schemas_hash(schemas)
    except Exception as e:
        return [f"schemas hash 계산 실패: {e}"]

    py_pat = re.compile(r'SOURCE_HASH\s*=\s*"([0-9a-f]{16})"')
    ts_pat = re.compile(r'export const SOURCE_HASH\s*=\s*"([0-9a-f]{16})"')
    for lang, rel in GENERATED_TARGETS:
        fp = WORKSPACE_ROOT / rel
        if not fp.exists():
            violations.append(f"{rel}  생성 파일 없음 — `gen_constants.py --all` 실행 필요")
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(f"{rel}  읽기 실패: {e}")
            continue
        m = (py_pat if lang == "python" else ts_pat).search(text)
        if not m:
            violations.append(f"{rel}  SOURCE_HASH 헤더 누락 — 수동 편집 의심")
            continue
        actual = m.group(1)
        if actual != expected_hash:
            violations.append(
                f"{rel}  SOURCE_HASH drift (file={actual} expected={expected_hash}) "
                f"— `gen_constants.py --all` 재실행 필요")
    return violations


# ── 3. JSON Schema 일관성 ───────────────────────────────────────────────────

STRATEGY_PATTERN_EXPECTED = r"^M(0[0-9]|1[0-5])$"


def check_schema_strategy_patterns() -> list[str]:
    """JSON Schema 파일이 구 패턴 ^M[0-8]$ 사용 시 위반 — pattern 키만 검사."""
    violations = []
    # "pattern": "^M[0-8]..." 형태만 매칭 (description 안의 설명문은 제외)
    bad_pattern = re.compile(r'"pattern"\s*:\s*"\^M\[0-8\]')
    for fp in SCHEMAS_DIR.glob("*.json"):
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if bad_pattern.search(line):
                violations.append(
                    f"{fp.name}:{lineno}  구 strategy pattern 발견: {line.strip()[:100]}")
    return violations


# ── 변경 파일 (pre-commit) ───────────────────────────────────────────────────

def changed_files() -> list[Path]:
    """git diff --cached --name-only 결과. CWD = pre-commit이 실행된 git repo 루트."""
    try:
        # 현재 작업 디렉토리의 git repo 루트를 찾음
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, encoding="utf-8").strip())
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(repo_root), text=True, encoding="utf-8")
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        p = repo_root / line
        if p.exists():
            files.append(p)
    return files


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check",
                    choices=["strategy", "ports", "schemas", "generated", "all"],
                    default="all")
    ap.add_argument("--pre-commit", action="store_true",
                    help="git diff --cached 대상만 검사")
    ap.add_argument("paths", nargs="*", help="검사할 경로 (기본: 워크스페이스 주요 프로젝트)")
    args = ap.parse_args()

    if args.paths:
        paths = [Path(p).resolve() for p in args.paths]
    elif args.pre_commit:
        paths = changed_files()
        if not paths:
            print("[SSOT] 변경 파일 없음, 통과")
            return 0
    else:
        # 기본 검사 대상
        paths = [
            WORKSPACE_ROOT / "projects" / p for p in
            ("edge-agent", "gridbridge", "building-energy-3d",
             "agentleague", "eduarena", "energy-contracts")
        ]
        paths = [p for p in paths if p.exists()]

    failed = False
    total_violations = 0

    if args.check in ("strategy", "all"):
        v = scan_legacy_strategies(paths)
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 구 전략 코드(M0~M8 단독) 발견: {len(v)}건")
            for fp, ln, snippet in v[:30]:
                rel = fp.relative_to(WORKSPACE_ROOT) if fp.is_absolute() else fp
                print(f"  {rel}:{ln}  {snippet}")
            if len(v) > 30:
                print(f"  ... 외 {len(v)-30}건 (총 {len(v)})")

    if args.check in ("ports", "all"):
        v = check_port_conflicts()
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 포트 충돌: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if args.check in ("schemas", "all"):
        v = check_schema_strategy_patterns()
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 스키마 패턴 위반: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if args.check in ("generated", "all"):
        v = check_generated_drift()
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] _generated_constants drift: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if failed:
        print(f"\n[SSOT] 위반 총 {total_violations}건 — 커밋 차단")
        return 1
    print("[SSOT] 모든 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
