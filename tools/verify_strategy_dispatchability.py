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

#: **현재 승인된 격차** — 화면은 내주지만 엣지가 못 하는 코드.
#  ⚠ 이 목록은 *정당화*가 아니라 *기록*이다. 줄어들어야 하고, 늘면 실패한다.
#  (2026-08-16 실측. 근거 = 공모전 docs/MCODE_ACCEPTANCE_HANDOVER_2026-08-16.md §5)
KNOWN_GAP = {
    "M01", "M03", "M05", "M06", "M07", "M08", "M10",
    "M11", "M12", "M13", "M14", "M15", "M21", "M22",
}


def canon_codes() -> set[str]:
    return set(json.loads(CANON.read_text(encoding="utf-8"))["default"]["strategies"])


def edge_codes() -> set[str]:
    """`_VALID_STRATEGIES` 를 **실행 없이** 읽는다(import 부작용 차단)."""
    tree = ast.parse(EDGE_SERVER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_VALID_STRATEGIES":
                    return set(ast.literal_eval(node.value))
    raise LookupError(f"{EDGE_SERVER.name} 에서 `_VALID_STRATEGIES` 를 못 찾았다")


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

    gap = sorted(ui - edge)
    unknown = sorted(set(gap) - KNOWN_GAP)
    closed = sorted(KNOWN_GAP - set(gap))
    stray = sorted(edge - canon)

    print(f"\n  격차(화면에 있으나 엣지가 거부)  {len(gap)}종")
    print(f"     {' '.join(gap) if gap else '없음'}")
    if stray:
        print(f"  ⛔ 엣지가 **정본에 없는 코드**를 받는다: {' '.join(stray)}")
    if closed:
        print(f"  ✅ 좁혀진 격차: {' '.join(closed)} — KNOWN_GAP 에서 빼라(그래야 되돌아가지 않는다)")

    print("-" * 74)
    bad = bool(unknown) or bool(stray) or bool(closed)
    if unknown:
        print(f"⛔ **새 격차 {len(unknown)}종**: {' '.join(unknown)}")
        print("   화면이 내주기 시작했는데 엣지가 못 하는 전략이 늘었다.")
    if not bad:
        print(f"✅ 격차 {len(gap)}종 — 기록된 그대로다(늘지 않음).")
        print("   ⚠ 이건 **격차가 없다는 뜻이 아니다.** 해소 계획은")
        print("     공모전 docs/MCODE_ACCEPTANCE_HANDOVER_2026-08-16.md §5.")
        return 0
    return 1 if a.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
