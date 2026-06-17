#!/usr/bin/env python
"""energy-contracts pin 일괄 bump 오케스트레이터 (P4, 2026-06-17 skew 재발 방지).

부분 cascade(한 consumer 만 pin bump / regen 누락) 가 2026-06-17 의 CI-only skew 를
유발했다. 본 스크립트는 새 energy-contracts 태그 릴리스 시 cascade 를 원자적으로 수행:

  1) 전 consumer pyproject.toml 의 energy-contracts pin 을 target 태그로 통일
  2) gen_constants.py --all 로 _generated_constants 전부 regen
  3) validate_ssot.py --check generated 로 pin↔regen lockstep 재검증 (P1 게이트)
  4) mirror 키워드 cascade 안내 (CORE_KEYWORDS 변경 시 sibling CLAUDE.md 헤더 갱신 필요)

사용:
  python bump_ec_pin.py v0.3.6           # 일괄 bump + regen + 검증
  python bump_ec_pin.py v0.3.6 --check   # dry-run (변경 미적용, 현 pin 진단만)

종료: 0 통과 / 1 위반·실패 / 2 인자 오류
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]
PROJECTS = WORKSPACE_ROOT / "projects"

# validate_ssot.EC_PIN_CONSUMERS 와 동기 (lockstep 그룹)
CONSUMERS = ("edge-agent", "gridbridge", "building-energy-3d")
_PIN_RE = re.compile(r"(energy-contracts.*?@)(v[0-9][\w.\-]*)")


def _pyproject(repo: str) -> Path:
    return PROJECTS / repo / "pyproject.toml"


def current_pins() -> dict[str, str | None]:
    pins: dict[str, str | None] = {}
    for repo in CONSUMERS:
        pp = _pyproject(repo)
        if not pp.exists():
            pins[repo] = None
            continue
        m = _PIN_RE.search(pp.read_text(encoding="utf-8"))
        pins[repo] = m.group(2) if m else None
    return pins


def bump_pins(target: str) -> list[str]:
    changed: list[str] = []
    for repo in CONSUMERS:
        pp = _pyproject(repo)
        if not pp.exists():
            continue
        txt = pp.read_text(encoding="utf-8")
        new = _PIN_RE.sub(lambda m: m.group(1) + target, txt)
        if new != txt:
            pp.write_text(new, encoding="utf-8", newline="\n")
            changed.append(repo)
    return changed


def run(cmd: list[str]) -> int:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(CONTRACTS_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="energy-contracts pin 일괄 bump 오케스트레이터")
    ap.add_argument("target", nargs="?", help="목표 태그 (예: v0.3.6)")
    ap.add_argument("--check", action="store_true", help="dry-run — 현 pin 진단만")
    args = ap.parse_args()

    pins = current_pins()
    print("[bump_ec_pin] 현재 pin:")
    for r, p in pins.items():
        print(f"  {r:22} {p}")

    if args.check:
        distinct = {p for p in pins.values() if p}
        if len(distinct) > 1:
            print(f"\n[bump_ec_pin] ✗ pin lockstep 위반: {distinct} — bump 필요")
            return 1
        print("\n[bump_ec_pin] ✓ pin lockstep OK")
        return 0

    if not args.target:
        print("\n[bump_ec_pin] target 태그 필요 (예: python bump_ec_pin.py v0.3.6)")
        return 2
    if not re.fullmatch(r"v[0-9][\w.\-]*", args.target):
        print(f"[bump_ec_pin] 태그 형식 오류: {args.target}")
        return 2

    print(f"\n[bump_ec_pin] → {args.target} 일괄 bump")
    changed = bump_pins(args.target)
    print(f"  변경: {changed or '없음(이미 동일)'}")

    print("\n[bump_ec_pin] regen (gen_constants.py --all):")
    if run([sys.executable, "scripts/gen_constants.py", "--all"]) != 0:
        print("[bump_ec_pin] ✗ regen 실패")
        return 1

    print("\n[bump_ec_pin] lockstep 재검증 (validate_ssot.py --check generated):")
    rc = run([sys.executable, "scripts/validate_ssot.py", "--check", "generated"])
    if rc != 0:
        print("[bump_ec_pin] ✗ 검증 실패 — pin 태그가 커밋 constants 를 커버하는지 확인")
        return 1

    print("\n[bump_ec_pin] ✓ 완료. ⚠ CORE_KEYWORDS 가 바뀐 릴리스라면 sibling CLAUDE.md "
          "mirror 헤더도 갱신할 것 (ai-champion-2026 cross-folder-drift-verify 게이트).")
    print("  다음: 각 consumer repo 에서 변경분 커밋 + PR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
