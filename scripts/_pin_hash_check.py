#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""**핀한 태그가 실제로 커밋된 SOURCE_HASH 를 만드는가.**

## 왜 따로 있는가 — lockstep 검사의 사각

`bump_ec_pin.py` 의 lockstep 검사는 **핀끼리 같은지**만 봤다.
*핀이 서로 같은 것*과 *핀이 옳은 것*은 다른 질문인데, 후자를 아무도 안 물었다.

2026-08-16 실측으로 그 사각이 드러났다:

    전 소비자 pin = v0.3.39      → lockstep 검사 **✓ 통과**
    커밋된 SOURCE_HASH = e612a519bde61458  (master, 스키마 33 종)
    v0.3.39 의 스키마 해시  = 02246e19d4efcab2  (스키마 32 종)

즉 CI 가 pin 대로 checkout 하면 **전 소비자에서 DRIFT** 가 나는 상태였는데
게이트는 초록이었다. 사고는 검사가 없는 자리에서 난다.

이 모듈은 태그를 임시 worktree 로 꺼내 그 시점 `gen_constants` 의 스키마 해시를
계산하고, 소비자가 커밋해 둔 `SOURCE_HASH` 와 대조한다.

⚠ 태그를 못 꺼내는 등 **잴 수 없는 상황은 생략(0)** 으로 답한다. 못 재는 것을
  위반으로 부르면 오프라인·얕은 clone 에서 게이트가 통째로 막힌다. 다만 생략은
  화면에 남긴다 — 조용한 생략이 곧 가짜 초록이다.
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_HASH_RE = re.compile(r'SOURCE_HASH\s*=\s*"([0-9a-f]+)"')


def committed_source_hashes(projects: Path, consumers) -> set[str]:
    """소비자들이 **커밋해 둔** 생성상수 해시 모음."""
    found: set[str] = set()
    for repo in consumers:
        root = projects / repo
        if not root.exists():
            continue
        for gen in root.rglob("_generated_constants.py"):
            if "node_modules" in str(gen):
                continue
            m = _HASH_RE.search(gen.read_text(encoding="utf-8", errors="replace"))
            if m:
                found.add(m.group(1))
    return found


def tag_schema_hash(contracts_root: Path, tag: str) -> str | None:
    """`tag` 시점의 스키마 해시. 못 재면 None."""
    tmp = Path(tempfile.mkdtemp(prefix="ec_pin_"))
    wt = tmp / "wt"
    try:
        r = subprocess.run(["git", "-C", str(contracts_root), "worktree", "add",
                            "--detach", str(wt), tag], capture_output=True)
        if r.returncode != 0:
            return None
        spec = importlib.util.spec_from_file_location(
            "_gc_tag", wt / "scripts" / "gen_constants.py")
        if spec is None or spec.loader is None:
            return None
        gc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gc)
        return gc.schemas_hash(gc.load_schemas())
    except Exception:                                    # noqa: BLE001
        return None
    finally:
        subprocess.run(["git", "-C", str(contracts_root), "worktree", "remove",
                        "--force", str(wt)], capture_output=True)
        subprocess.run(["git", "-C", str(contracts_root), "worktree", "prune"],
                       capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def check(contracts_root: Path, projects: Path, consumers, tag: str | None) -> int:
    """0 통과·생략 / 1 위반."""
    if not tag:
        print("  ⚠ 핀이 하나로 모이지 않아 태그↔해시 검증 생략")
        return 0

    have = committed_source_hashes(projects, consumers)
    if not have:
        print("  ⚠ 커밋된 SOURCE_HASH 를 못 찾아 태그↔해시 검증 생략")
        return 0
    if len(have) > 1:
        print(f"  ✗ 소비자들의 SOURCE_HASH 가 갈라져 있다: {sorted(have)}")
        return 1

    th = tag_schema_hash(contracts_root, tag)
    if th is None:
        print(f"  ⚠ 태그 {tag} 를 꺼내지 못해 태그↔해시 검증 생략")
        return 0

    mine = have.pop()
    if th != mine:
        print(f"  ✗ 핀한 {tag} 는 커밋된 상수를 재현하지 못한다")
        print(f"      {tag} 스키마 해시     = {th}")
        print(f"      소비자 SOURCE_HASH  = {mine}")
        print("    → CI 가 pin 대로 checkout 하면 전 소비자에서 DRIFT 가 난다.")
        print("       새 태그를 릴리스해 bump 하거나, 상수를 그 태그로 regen 하라.")
        return 1
    print(f"  태그↔해시 재현 확인: {tag} → {th}")
    return 0
