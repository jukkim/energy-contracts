#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""화면이 내주는 전략과 엣지가 **실제로 할 수 있는** 전략이 같은가.

## 왜 이 가드가 있는가

M-code 의미를 전 저장소에서 하나로 맞췄다. 그런데 **의미가 하나여도 안전해지지
않는다** — 이름이 같아도 *부를 수 있는 것*과 *할 수 있는 것*이 다르면, 운영자는
화면에서 고를 수 있는 전략을 눌렀는데 엣지가 거부한다.

실측(2026-08-16):

    UI/op_registry enum    M00|M01|…|M21|M22        23 종 전부 제공
    edge-agent 수용         _VALID_STRATEGIES        9 종
    차이                    14 종

그리고 거부 메시지가 원인을 안 알려준다 —
`"strategy 는 M00~M20 이어야 함"` 인데 **M01 은 그 범위 안인데도 거부**된다.

제어 계통에서 이 차이는 라벨 오류보다 위험하다. 라벨은 틀린 이름을 보여줄 뿐이지만,
이건 **누를 수 있는 버튼이 아무 일도 안 하는 것**이다.

## 이 도구가 하는 일 / 하지 않는 일

- **한다**: 격차를 재고, **기록된 격차보다 커지면 실패**시킨다.
- **하지 않는다**: 계약을 바꾸지 않는다. 상태 코드(400→422)·스키마 필드
  (`dispatchable`)·UI 동작을 바꾸는 건 제품 결정이라 사람이 정한다.

즉 **지금 있는 격차를 승인하는 게 아니라, 조용히 자라는 것을 막는다.**
격차를 줄이면 `KNOWN_GAP` 도 함께 줄여야 통과한다(한 방향으로만 움직인다).

사용:
    python tools/verify_strategy_dispatchability.py
    python tools/verify_strategy_dispatchability.py --strict   # 격차 확대 시 exit 1
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve()
EC_ROOT = HERE.parents[1]
WORKSPACE = EC_ROOT.parents[1]

CANON = EC_ROOT / "energy_contracts" / "schemas" / "ems_strategies.json"
EDGE_SERVER = WORKSPACE / "projects" / "edge-agent" / "src" / "api" / "server.py"
OP_REGISTRY = (WORKSPACE / "projects" / "building-energy-3d-lab" /
               "src" / "_shared" / "op_registry.json")

CAPABILITY = EC_ROOT / "energy_contracts" / "schemas" / "edge_strategy_capability.json"


def declared() -> tuple[set[str], dict[str, str]]:
    """**선언된** 실행 가능 집합과 못 하는 사유. 단일 출처."""
    d = json.loads(CAPABILITY.read_text(encoding="utf-8"))
    return set(d["dispatchable"]), dict(d["not_dispatchable"])


def canon_codes() -> set[str]:
    return set(json.loads(CANON.read_text(encoding="utf-8"))["default"]["strategies"])


def edge_codes() -> set[str]:
    """엣지가 **실제로 쓰는** 집합.

    ⚠ 예전엔 소스에서 리터럴을 `ast.literal_eval` 로 긁었다. 값이 계약 파일에서
      파생되도록 바뀌자(`_VALID_STRATEGIES = _load_dispatchable()`) 그 방식은
      **터졌다** — 다행히 조용히 통과하지 않고 예외를 냈다.
      정적 파싱은 "지금 무엇이 쓰이는지" 를 못 본다. **실행해서 읽는다.**
    """
    src = EDGE_SERVER.parents[1]
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    import importlib

    mod = importlib.import_module("api.server")
    got = set(getattr(mod, "_VALID_STRATEGIES", ()))
    if not got:
        raise LookupError("edge `_VALID_STRATEGIES` 가 비었다")
    return got


def ui_codes() -> set[str]:
    """op_registry 의 strategy enum(파이프 구분 문자열)에서 코드를 뽑는다."""
    txt = OP_REGISTRY.read_text(encoding="utf-8")
    best: set[str] = set()
    for m in re.finditer(r'"strategy"\s*:\s*"([^"]*M\d\d[^"]*)"', txt):
        codes = set(re.findall(r"M\d\d", m.group(1)))
        if len(codes) > len(best):
            best = codes
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="전략 실행 가능성 격차 가드")
    ap.add_argument("--strict", action="store_true", help="격차 확대 시 exit 1")
    a = ap.parse_args(argv)

    canon, edge, ui = canon_codes(), edge_codes(), ui_codes()

    print("=" * 74)
    print("전략 실행 가능성 — 화면이 내주는 것 vs 엣지가 할 수 있는 것")
    print("=" * 74)
    print(f"  정본            {len(canon)}종")
    print(f"  UI enum        {len(ui)}종")
    print(f"  edge 수용       {len(edge)}종  {' '.join(sorted(edge))}")

    # ⚠ 검사 대상이 비면 통과가 아니다 — 파싱이 어긋난 채 초록을 내면 안 된다.
    if not canon or not edge or not ui:
        print("\n⛔ 어느 한쪽을 0 종으로 읽었다 — 파싱이 어긋났다(가드가 공허하다).")
        return 1

    decl, reasons = declared()
    gap = sorted(ui - edge)
    undeclared = sorted((canon - decl) - set(reasons))
    stray = sorted(edge - canon)
    drift_edge = sorted(edge ^ decl)
    drift_ui = sorted(ui - decl)

    print("")
    print(f"  선언(계약)      {len(decl)}종 실행 가능 · {len(reasons)}종 사유 기재")
    print(f"  UI ↔ edge 격차   {len(gap)}종  {' '.join(gap) if gap else '**없음**'}")
    if drift_edge:
        print(f"  ⛔ edge 가 선언과 다르다: {' '.join(drift_edge)}")
    if drift_ui:
        print(f"  ⛔ UI 가 선언에 없는 걸 내준다: {' '.join(drift_ui)}")
    if undeclared:
        print(f"  ⛔ 정본에 있는데 **선언도 사유도 없는** 코드: {' '.join(undeclared)}")
    if stray:
        print(f"  ⛔ edge 가 정본 밖 코드를 받는다: {' '.join(stray)}")

    print("-" * 74)
    bad = bool(gap) or bool(drift_edge) or bool(drift_ui) or bool(undeclared) or bool(stray)
    if not bad:
        print(f"✅ 화면이 내주는 전략 = 엣지가 할 수 있는 전략 ({len(decl)}종). 격차 0.")
        print(f"   못 하는 {len(reasons)}종은 **사유와 함께** 계약에 적혀 있다 —")
        print("   화면에서 아예 내주지 않으므로 '눌러도 아무 일 없는 버튼'이 없다.")
        return 0
    print("⛔ 화면과 엣지가 어긋난다. 단일 출처 = edge_strategy_capability.json")
    return 1 if a.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
