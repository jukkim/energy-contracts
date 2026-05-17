"""Phase M-4: _generated_constants exports 사용 현황 조사.

각 repo 의 _generated_constants.{py,ts} 에서 export 심볼을 추출하고,
같은 repo 의 소스(_generated_constants 자기 자신 제외)에서 그 심볼이
실제로 참조되는지 grep 으로 확인.

산출물: scratch/m4_exports_audit.json — 프로젝트별 used/dead 분류
        + 콘솔에 비율 요약 표.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]
SCRATCH_DIR = CONTRACTS_ROOT / "scratch"

# (project, generated_path, scan_root, is_ts)
# scan_root = repo 전체 (tests 포함, _generated_constants.* 만 제외)
TARGETS = [
    ("edge-agent",         "projects/edge-agent/src/_generated_constants.py",
                           "projects/edge-agent",                           False),
    ("gridbridge",         "projects/gridbridge/src/_generated_constants.py",
                           "projects/gridbridge",                           False),
    ("building-energy-3d-py", "projects/building-energy-3d/src/shared/_generated_constants.py",
                              "projects/building-energy-3d",                False),
    ("building-energy-3d-ts", "projects/building-energy-3d/frontend/src/shared/_generated_constants.ts",
                              "projects/building-energy-3d/frontend",       True),
    ("agentleague",        "projects/agentleague/backend/_generated_constants.py",
                           "projects/agentleague",                          False),
    ("eduarena",           "projects/eduarena/backend/_generated_constants.py",
                           "projects/eduarena",                             False),
]

PY_EXPORT_RE = re.compile(r"^([A-Z][A-Z0-9_]*)(?:\s*:|\s*=)", re.M)
TS_EXPORT_RE = re.compile(r"^export\s+const\s+([A-Z][A-Z0-9_]*)", re.M)


def extract_exports(fp: Path, is_ts: bool) -> list[str]:
    text = fp.read_text(encoding="utf-8")
    pat = TS_EXPORT_RE if is_ts else PY_EXPORT_RE
    return sorted(set(pat.findall(text)))


SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx"}
SKIP_DIRS = {"node_modules", "dist", ".git", ".venv", "venv", "env",
             "__pycache__", "build", "site-packages", ".next", "out",
             "coverage", ".pytest_cache", ".mypy_cache", ".turbo",
             # 형제 _generated_constants 파일 (다른 위치도) 도 모두 제외
             }
GENERATED_NAMES = {"_generated_constants.py", "_generated_constants.ts"}


def _iter_files(scan_root: Path, exclude: Path):
    for p in scan_root.rglob("*"):
        if not p.is_file() or p.suffix not in SCAN_EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in GENERATED_NAMES:
            continue  # 같은 또는 다른 위치의 _generated_constants 파일 자체 제외
        if p.resolve() == exclude.resolve():
            continue
        yield p


def search_usage(symbol: str, scan_root: Path, exclude: Path,
                 file_cache: dict[Path, str]) -> int:
    """심볼이 scan_root 하위 (exclude 제외) 에서 whole-word 로 몇 번 등장하는지."""
    if not scan_root.exists():
        return 0
    pat = re.compile(rf"\b{re.escape(symbol)}\b")
    total = 0
    for fp in _iter_files(scan_root, exclude):
        if fp not in file_cache:
            try:
                file_cache[fp] = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                file_cache[fp] = ""
        total += len(pat.findall(file_cache[fp]))
    return total


def main() -> int:
    SCRATCH_DIR.mkdir(exist_ok=True)
    audit: dict = {}
    rows: list[tuple[str, int, int, int]] = []  # (project, total, used, dead)
    for proj, gen_rel, scan_rel, is_ts in TARGETS:
        gen_fp = WORKSPACE_ROOT / gen_rel
        scan_root = WORKSPACE_ROOT / scan_rel
        if not gen_fp.exists():
            print(f"[m4] SKIP {proj}: {gen_rel} 없음")
            continue
        exports = extract_exports(gen_fp, is_ts)
        # 항상 hash 헤더 SOURCE_HASH 는 SSOT drift 검사용 필수 → used 로 강제 표시
        always_keep = {"SOURCE_HASH"}
        file_cache: dict[Path, str] = {}
        usage: dict[str, int] = {}
        for sym in exports:
            if sym in always_keep:
                usage[sym] = -2  # 강제 유지
                continue
            usage[sym] = search_usage(sym, scan_root, gen_fp, file_cache)
        used = [s for s, n in usage.items() if n != 0]
        dead = [s for s, n in usage.items() if n == 0]
        audit[proj] = {
            "generated_path": gen_rel,
            "scan_root": scan_rel,
            "total": len(exports),
            "used": used,
            "dead": dead,
            "usage_counts": usage,
        }
        rows.append((proj, len(exports), len(used), len(dead)))

    out_fp = SCRATCH_DIR / "m4_exports_audit.json"
    out_fp.write_text(json.dumps(audit, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\n[m4] 감사 결과: {out_fp.relative_to(WORKSPACE_ROOT)}")

    # 요약 표
    print(f"\n{'project':<25} {'total':>6} {'used':>6} {'dead':>6} {'dead %':>8}")
    print("-" * 60)
    for proj, total, used, dead in rows:
        pct = (dead / total * 100) if total else 0
        print(f"{proj:<25} {total:>6} {used:>6} {dead:>6} {pct:>7.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
