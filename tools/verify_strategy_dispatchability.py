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

#: 제품·발표가 읽는 M-code 상태 문서. 여기 적힌 숫자가 계약과 어긋나면 **밖에서 들킨다**.
#  2026-08-17: 이 문서에는 명칭 통일만 적혀 있고 "실제로 몇 종이 실행되는가" 가 없었다.
#  그래서 "M-code 통일 완료" 를 읽은 사람이 23 종을 다 발령할 수 있다고 이해할 수 있었다.
STATUS_DOC = (WORKSPACE / "공모전" / "2026-04-24_AI챔피언_전국민AI경진대회" /
              "docs" / "MCODE_UNIFICATION_PLAN_2026-08-15.md")
#: ⚠ `\s+` 는 개행도 먹는다. blocked 목록이 **빈** 판에서 다음 줄(```)을 삼켜
#   "문서에만 ['```']" 이라는 엉뚱한 불일치를 냈다(2026-08-17 실측).
#   줄 안에서만 움직이도록 `[ \t]` 로 고정한다.
STATUS_BLOCK_RE = re.compile(
    r"MCODE-DISPATCH-STATUS v1[ \t]*\n"
    r"[ \t]*canonical[ \t]+(\d+)[ \t]+([^\n]*)\n"
    r"[ \t]*dispatchable[ \t]+(\d+)[ \t]+([^\n]*)\n"
    r"[ \t]*blocked[ \t]+(\d+)[ \t]*([^\n]*)")


def doc_status() -> dict | None:
    """상태 문서의 기계 판독 블록. 없으면 None(호출부가 실패로 처리)."""
    if not STATUS_DOC.exists():
        return None
    m = STATUS_BLOCK_RE.search(STATUS_DOC.read_text(encoding="utf-8", errors="replace"))
    if not m:
        return None
    return {
        "canonical_n": int(m.group(1)), "canonical": set(m.group(2).split()),
        "dispatchable_n": int(m.group(3)), "dispatchable": set(m.group(4).split()),
        "blocked_n": int(m.group(5)), "blocked": set(m.group(6).split()),
    }


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


def check_capability_tiers() -> list[str]:
    """**단계가 뭉개지지 않았는가** (2026-08-17 외부 재감사 지적 수용).

    `dispatchable: 23` 을 전역 사실로 읽으면 현장(BACnet·Modbus 기본 맵 10 종)보다
    넓어진다. 계약이 단계를 갈라 적고, 그 구분이 **살아 있는지** 여기서 지킨다.

    ⚠ 특히 `READBACK_VERIFIED`·`MV_VERIFIED` 가 0 이 아닌 값으로 바뀌면 그건
      **새 기능이 생겼다**는 뜻이므로 증거를 요구해야 한다 — 숫자만 올리는 것을 막는다.
    """
    try:
        d = json.loads(CAPABILITY.read_text(encoding="utf-8"))
    except Exception as e:                                # noqa: BLE001
        return [f"capability 계약을 못 읽었다: {e}"]

    tiers = d.get("capability_tiers")
    if not tiers:
        return ["`capability_tiers` 가 없다 — 'dispatchable 23' 이 전역 사실로 읽힌다"]

    v: list[str] = []
    for k in ("CANONICAL", "REFERENCE_DISPATCHABLE", "SITE_DISPATCHABLE",
              "READBACK_VERIFIED", "MV_VERIFIED"):
        if k not in tiers:
            v.append(f"capability_tiers 에 `{k}` 단계가 없다")
    if not d.get("dispatchable_semantics"):
        v.append("`dispatchable_semantics` 가 없다 — 최상위 목록의 뜻을 계약이 말하지 않는다")
    # 아직 없는 단계가 **조용히 켜지는 것**을 막는다.
    for k in ("READBACK_VERIFIED", "MV_VERIFIED"):
        c = (tiers.get(k) or {}).get("count")
        if isinstance(c, int) and c > 0:
            v.append(f"`{k}` 가 {c} 로 켜졌다 — 그 단계의 증거(되읽기·M&V 필드)를 "
                     f"먼저 제시해야 한다")
    return v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="전략 실행 가능성 격차 가드")
    ap.add_argument("--strict", action="store_true", help="격차 확대 시 exit 1")
    ap.add_argument("--check-docs", action="store_true",
                    help="상태 문서의 숫자·목록이 계약과 같은지도 본다")
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

    tier_bad = check_capability_tiers()
    print()
    print(f"  단계 구분      {'✅ CANONICAL/REFERENCE/SITE/READBACK/MV 5단계 선언' if not tier_bad else '⛔ ' + str(len(tier_bad)) + '건'}")
    for m in tier_bad:
        print(f"    · {m}")

    doc_bad: list[str] = []
    if a.check_docs:
        d = doc_status()
        if d is None:
            doc_bad.append(f"상태 문서에서 MCODE-DISPATCH-STATUS 블록을 못 읽었다 "
                           f"({STATUS_DOC.name}) — 문서가 상태를 안 적고 있다")
        else:
            blocked = set(reasons)
            checks = [
                ("canonical 목록", d["canonical"], canon),
                ("dispatchable 목록", d["dispatchable"], decl),
                ("blocked 목록", d["blocked"], blocked),
            ]
            for label, got, want in checks:
                if got != want:
                    doc_bad.append(f"{label} 불일치 — 문서에만 {sorted(got - want)} · "
                                   f"계약에만 {sorted(want - got)}")
            counts = [("canonical", d["canonical_n"], len(canon)),
                      ("dispatchable", d["dispatchable_n"], len(decl)),
                      ("blocked", d["blocked_n"], len(blocked))]
            for label, got_n, want_n in counts:
                if got_n != want_n:
                    doc_bad.append(f"{label} 개수 불일치 — 문서 {got_n} · 계약 {want_n}")
        print("")
        print(f"  상태 문서 대조   {'⛔ ' + str(len(doc_bad)) + '건 어긋남' if doc_bad else '✅ 계약과 일치'}")
        for m in doc_bad:
            print(f"    · {m}")

    print("-" * 74)
    bad = (bool(gap) or bool(drift_edge) or bool(drift_ui) or bool(undeclared)
           or bool(stray) or bool(doc_bad) or bool(tier_bad))
    if not bad:
        print(f"✅ 화면이 내주는 전략 = 엣지가 할 수 있는 전략 ({len(decl)}종). 격차 0.")
        print(f"   못 하는 {len(reasons)}종은 **사유와 함께** 계약에 적혀 있다 —")
        print("   화면에서 아예 내주지 않으므로 '눌러도 아무 일 없는 버튼'이 없다.")
        return 0
    if doc_bad and not (gap or drift_edge or drift_ui or undeclared or stray):
        print("⛔ 코드는 맞는데 **문서가 다른 숫자를 말한다.** 문서를 계약에 맞출 것 —")
        print(f"   {STATUS_DOC.relative_to(WORKSPACE)} §2.5")
        return 1 if a.strict else 0
    print("⛔ 화면과 엣지가 어긋난다. 단일 출처 = edge_strategy_capability.json")
    return 1 if a.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
