#!/usr/bin/env python
"""계보 봉투 **사본이 정본과 바이트 동일한가** (등재 #29, 2026-09-04).

## 왜 사본인가 (import 가 아니라)

저장소마다 `energy_contracts` **설치본 버전이 다르다** — 실측 2026-09-04:
워크스페이스 소스 `0.3.50` ↔ be-3d 설치본 `0.3.46`. import 로 두면 낡은 설치본에서
계약이 **조용히 사라지고**, 그러면 봉투 없이 나가는 경로가 다시 생긴다. 그것이
바로 #29 를 한 번 "닫았다" 고 했다가 철회한 이유다(붙였다던 게 검증 없는 dict 였고
DB·API 로 나가지도 않았다).

사본 + 해시 게이트 = 전역 SSOT 룰의 「guarded mirror + verify_*_mirror」 파이썬 판.

## ⚠ 이 게이트가 **보는 것**과 못 보는 것

  본다     정본 ↔ 사본의 바이트 동일성 · 사본의 존재
  못 본다  라벨의 진실성(`measured` 가 정말 실측인지) — **집계 코드의 책임**이다

「게이트가 맞는 것을 보는지 확인하라」 — 이 게이트를 시험하려면 사본 한 글자를
바꾸고 exit 1 이 나는지 보라(`--selftest` 가 임시 파일로 그 왕복을 한다).

exit 0 = 전부 동일 · 1 = 드리프트 · 2 = **못 잼**(사본 파일 부재 = 통과 아님)
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

#: 워크스페이스 루트 = 이 파일에서 3단계 위(`projects/energy-contracts/scripts/`)
_ROOT = Path(__file__).resolve().parents[3]
CANON = (_ROOT / "projects" / "energy-contracts" / "energy_contracts"
         / "provenance" / "envelope.py")
#: ⛔ 사본을 늘리면 **여기 등재**한다. 등재 안 된 사본은 이 게이트가 못 본다.
VENDORS = (
    _ROOT / "8.simulation" / "ems_transformer" / "serving" / "_provenance_envelope.py",
    _ROOT / "projects" / "building-energy-3d" / "src" / "shared" / "provenance_envelope.py",
    #: 2026-09-04 — ingestion-worker 집계 provenance API (등재 #29·#36).
    #  필지 종합집계(`gold.pnu_summary`)를 집계 단위 봉투로 내보내는 경로가
    #  생기면서 이 저장소도 사본을 갖는다.
    _ROOT / "projects" / "ingestion-worker" / "src" / "shared" / "provenance_envelope.py",
)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check() -> int:
    if not CANON.is_file():
        print(f"[UNMEASURED] 정본이 없다: {CANON}")
        return 2
    want = _sha(CANON)
    print(f"정본 {want[:12]}  {CANON.relative_to(_ROOT)}")
    rc = 0
    for v in VENDORS:
        if not v.is_file():
            #: ⛔ 사본이 없는 것은 통과가 아니다 — 그 저장소는 계약 없이 도는 것이다.
            print(f"  [UNMEASURED] 사본 없음: {v}")
            rc = max(rc, 2)
            continue
        got = _sha(v)
        ok = got == want
        print(f"  {'OK   ' if ok else 'DRIFT'} {got[:12]}  {v.relative_to(_ROOT)}")
        if not ok:
            rc = max(rc, 1)
    if rc == 0:
        print("계보 봉투 사본 = 정본 (드리프트 0)")
    else:
        print("\n고치는 법: 정본을 고친 뒤 사본에 복사한다(반대 방향 금지).")
        for v in VENDORS:
            print(f"  cp '{CANON}' '{v}'")
    return rc


def selftest() -> int:
    """⛔ **게이트가 실제로 빨개지는가** — 변이 시험을 파일로 남긴다.

    셸 일회성 실행은 자산이 아니다(전역 룰). 사본 하나를 한 글자 바꿔 exit 1 이
    나는지 보고 **반드시 되돌린다**.
    """
    target = next((v for v in VENDORS if v.is_file()), None)
    if target is None:
        print("[UNMEASURED] 변이시킬 사본이 없다")
        return 2
    orig = target.read_bytes()
    try:
        target.write_bytes(orig + b"\n# mutation\n")
        rc = check()
        if rc != 1:
            print(f"[FAIL] 변이시켰는데 게이트가 rc={rc} 다 — 이 게이트는 안 본다")
            return 1
        print("[selftest] 변이 → exit 1 확인")
    finally:
        target.write_bytes(orig)
    rc2 = check()
    if rc2 != 0:
        print(f"[FAIL] 복원했는데 rc={rc2} — 원본을 되돌리지 못했다")
        return 1
    print("[selftest] 복원 → exit 0 확인. 양방향 통과")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true",
                    help="사본을 변이시켜 게이트가 빨개지는지 본 뒤 되돌린다")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else check())
