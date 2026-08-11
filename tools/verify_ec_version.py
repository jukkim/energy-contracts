#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""설치된 energy-contracts 가 워크스페이스 SSOT 와 같은 버전인가.

배경(2026-08-11 23 폴더 감사): 소비 repo 6 종 **어디도 energy-contracts 를 핀하지 않는다.**
그래서 무엇이 깔려 있든 조용히 이긴다 — 감사는 "전역 0.1.0" 을 보고 GridBridge 15 건
실패를 보고했고, 같은 코드가 다른 환경(0.3.39)에서는 328 건 전부 통과했다.
**같은 코드가 환경에 따라 다른 결론을 내면 그 결론은 근거가 못 된다.**

그래서 계약을 읽기 전에 **무엇을 읽고 있는지** 먼저 말하게 한다.

판정:
  0 = 설치본 버전 == 저장소 SSOT 버전 (또는 미설치 = 이 repo 는 EC 를 안 쓴다)
  1 = 불일치 — 어느 계약을 읽는지 모르는 상태다
  2 = 저장소 SSOT 를 못 읽음(구조 손상)

사용:
    python tools/verify_ec_version.py
    python tools/verify_ec_version.py --quiet     # 불일치일 때만 출력
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def repo_version() -> str | None:
    py = REPO / "pyproject.toml"
    if not py.is_file():
        return None
    m = re.search(r'^version\s*=\s*"([^"]+)"', py.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def installed() -> tuple[str | None, str | None, str | None]:
    """(실제 로드된 코드의 버전, 로드 경로, 메타데이터가 말하는 버전).

    ⚠ `importlib.metadata.version()` 을 단독으로 믿으면 안 된다(2026-08-11 실측):
      repo 안에서 실행하면 **낡은 `energy_contracts.egg-info`** 를 읽어 0.3.25 를 주고,
      repo 밖에서는 site-packages 의 0.3.39 를 준다 — 같은 머신에서 답이 갈린다.
      **판정 기준은 실제로 import 된 코드**(`__version__`)다. 메타데이터는 참고로만 싣고,
      둘이 다르면 그 자체를 경고한다.
    """
    meta_ver = None
    try:
        import importlib.metadata as md
        meta_ver = md.version("energy-contracts")
    except Exception:                                   # noqa: BLE001
        pass
    try:
        import energy_contracts
        return (getattr(energy_contracts, "__version__", None),
                energy_contracts.__file__, meta_ver)
    except Exception:                                   # noqa: BLE001
        return None, None, meta_ver


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="energy-contracts 버전 정합 게이트")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    want = repo_version()
    if not want:
        print("FAIL — 저장소 pyproject.toml 에서 version 을 못 읽었다(구조 손상).")
        return 2

    got, where, meta_ver = installed()
    if got is None and meta_ver is None:
        if not args.quiet:
            print(f"SKIP — energy-contracts 미설치. (저장소 SSOT = {want})")
            print("       이 repo 가 계약을 쓰지 않는다면 정상이다.")
        return 0

    # 메타데이터가 실제 코드와 다르면 그것부터 말한다 — 이게 cwd 에 따라 답이 갈리는 함정이다.
    stale_meta = meta_ver is not None and got is not None and meta_ver != got
    if stale_meta:
        print(f"⚠ 메타데이터({meta_ver}) ≠ 실제 로드된 코드({got}).")
        print("   `importlib.metadata` 는 실행 위치에 따라 낡은 egg-info 를 읽는다 —")
        print("   버전을 그것으로 판정하는 도구는 cwd 에 따라 다른 답을 낸다.")
        print(f"   정리: rm -rf \"{REPO / 'energy_contracts.egg-info'}\" 후 재설치.")

    if got == want:
        if not args.quiet or stale_meta:
            print(f"PASS — 로드된 energy-contracts {got} (저장소 SSOT 와 일치)")
            if where:
                print(f"       로드 경로: {where}")
        return 0

    print("FAIL — 계약 버전 불일치. **지금 어느 계약을 읽는지 모르는 상태다.**")
    print(f"  저장소 SSOT : {want}   ({REPO / 'pyproject.toml'})")
    print(f"  설치본      : {got}")
    if where:
        print(f"  로드 경로   : {where}")
    print()
    print("→ 고치는 법:")
    print(f"     pip install -e \"{REPO}\"")
    print("   같은 코드가 환경에 따라 다른 결론을 내면 그 결론은 근거가 못 된다 —")
    print("   테스트 실패를 코드 결함으로 읽기 전에 이 줄부터 맞출 것.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
