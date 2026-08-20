#!/usr/bin/env python
"""energy-contracts pin 일괄 bump 오케스트레이터 (P4, 2026-06-17 skew 재발 방지).

부분 cascade(한 consumer 만 pin bump / regen 누락) 가 2026-06-17 의 CI-only skew 를
유발했다. 본 스크립트는 새 energy-contracts 태그 릴리스 시 cascade 를 원자적으로 수행:

  1) 전 consumer pyproject.toml 의 energy-contracts pin 을 target 태그로 통일
  2) 전 consumer .github/workflows/ssot-drift.yml 의 EC checkout `ref:` 를 동일 태그로 통일
  3) gen_constants.py --all 로 _generated_constants 전부 regen
  4) validate_ssot.py --check generated 로 pin↔regen lockstep 재검증 (P1 게이트)
  5) mirror 키워드 cascade 안내 (CORE_KEYWORDS 변경 시 sibling CLAUDE.md 헤더 갱신 필요)

(2) 는 2026-07-21·2026-07-31 두 차례 재발한 CI 함정의 근절책이다. pyproject pin 만
bump 하면 ssot-drift 워크플로가 **옛 태그의 스키마**로 gen_constants --check 를 돌려
regen 된 생성본을 DRIFT 로 오탐(또는 신규 상수를 못 보고 실패)한다. pin 과 ref 는
항상 같이 움직여야 한다.

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
#
# ⚠ 여기 없는 repo 가 워크플로에 `ref: vX.Y.Z` 를 박아 두면 **조용히 뒤처진다**
# (2026-08-01 실측: v0.3.29 bump 후 ingestion-worker 만 ssot-drift 빨간불 —
# pyproject 핀은 없는데 ssot-drift.yml 이 v0.3.27 을 고정하고 있었다).
# EC 를 checkout 하며 ref 를 고정하는 repo 는 **전부** 여기 있어야 한다.
#: ⚠ **mgcc 추가 (2026-08-02)** — 핀은 갖고 있는데 이 목록에 없어서
#: **lockstep 검사를 통째로 빠져나갔다**. 실제로 mgcc 만 v0.3.31, 나머지 4개는
#: v0.3.29 인 상태가 게이트에 안 걸린 채로 있었다(실측). 핀을 선언하는 repo 는
#: 여기 있어야 한다 — 없으면 조용히 갈라진다.
#: ⚠ **building-energy-sejong 추가 (2026-08-02)** — 생성 상수 소비자인데 핀이
#: CI YAML 안에만 있어 이 목록 밖이었다. 그 결과 M00~M20 에 멈추고 **배출계수
#: 0.4594 구값**으로 CO₂ 를 계산해 왔다(정본 0.4173). 핀을 pyproject 로 옮기고
#: 여기 등재해야 게이트가 이 repo 를 본다 — mgcc(#78) 와 같은 종류의 누락이다.
CONSUMERS = ("edge-agent", "gridbridge", "building-energy-3d", "ingestion-worker",
             "mgcc", "building-energy-sejong")
_PIN_RE = re.compile(r"(energy-contracts.*?@)(v[0-9][\w.\-]*)")
# ssot-drift.yml 의 EC checkout step — `repository: jukkim/energy-contracts` 뒤따르는
# `ref: vX.Y.Z`(주석 유무 무관). 다른 repo checkout 의 ref 는 건드리지 않는다.
# WARN **CRLF 를 못 보면 조용히 아무것도 안 한다.** `_read_keep_newlines` 는 줄끝을
#   일부러 보존하는데(파일을 통째로 재작성하지 않으려고), 이 정규식은 LF 만 봤다.
#   그래서 CRLF 로 체크아웃된 저장소에서는 매치가 안 되고, 도구는 "이미 동일"
#   이라고 답한다 — 고장도 아니고 경고도 없는 **무동작**이다.
#   실측(2026-08-20): edge-agent 만 CRLF 라 ref 가 v0.3.40 에 남았고, lockstep
#   검사가 그제서야 skew 를 잡았다. LF 인 저장소 둘은 멀쩡히 바뀌어 더 안 보였다.
_WF_REF_RE = re.compile(
    r"(repository:[^\S\r\n]*jukkim/energy-contracts\b"
    r"(?:[^\r\n]*\r?\n(?![^\S\r\n]*ref:)[^\r\n]*)*?"
    r"\r?\n[^\S\r\n]*ref:[^\S\r\n]*)(v[0-9][\w.\-]*)"
)


def _pyproject(repo: str) -> Path:
    return PROJECTS / repo / "pyproject.toml"


def _workflow(repo: str) -> Path:
    return PROJECTS / repo / ".github" / "workflows" / "ssot-drift.yml"


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


def current_wf_refs() -> dict[str, list[str]]:
    """consumer 별 ssot-drift.yml 의 EC checkout ref 목록(파일당 2회 이상 가능)."""
    refs: dict[str, list[str]] = {}
    for repo in CONSUMERS:
        wf = _workflow(repo)
        if not wf.exists():
            continue
        refs[repo] = [m.group(2) for m in _WF_REF_RE.finditer(wf.read_text(encoding="utf-8"))]
    return refs


def _read_keep_newlines(p: Path) -> str:
    """줄끝을 **번역하지 않고** 읽는다.

    ⚠ `read_text()` 는 CRLF 를 LF 로 바꿔 들여온다. 거기에 LF 고정 쓰기를 짝지으면
      CRLF 파일이 통째로 LF 가 된다 — 내용은 한 글자도 안 바뀌었는데 git 은 전 줄이
      바뀐 것으로 본다(2026-08-16 롤백 예행 중 실측: pin 왕복 후 `pyproject.toml`·
      `ssot-drift.yml` 이 '변경' 으로 남았다). 기준선 manifest 는 그걸
      **작업트리 오염**으로 읽는다 — 없는 오염을 만든다.
    """
    with p.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_keep_newlines(p: Path, s: str) -> None:
    with p.open("w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def bump_pins(target: str) -> list[str]:
    changed: list[str] = []
    for repo in CONSUMERS:
        pp = _pyproject(repo)
        if not pp.exists():
            continue
        txt = _read_keep_newlines(pp)
        new = _PIN_RE.sub(lambda m: m.group(1) + target, txt)
        if new != txt:
            _write_keep_newlines(pp, new)
            changed.append(repo)
    return changed


def bump_wf_refs(target: str) -> list[str]:
    """ssot-drift.yml 의 EC checkout ref 를 target 으로 통일 (pin 과 lockstep)."""
    changed: list[str] = []
    for repo in CONSUMERS:
        wf = _workflow(repo)
        if not wf.exists():
            continue
        txt = _read_keep_newlines(wf)
        new = _WF_REF_RE.sub(lambda m: m.group(1) + target, txt)
        if new != txt:
            _write_keep_newlines(wf, new)
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
    wf_refs = current_wf_refs()
    print("[bump_ec_pin] 현재 pin / ssot-drift ref:")
    for r, p in pins.items():
        refs = wf_refs.get(r) or ["(ref 없음)"]
        # ⚠ **핀이 없는 소비자가 있다.** 그대로 `{p:12}` 로 찍으면 None 포맷에서
        #   TypeError 로 죽는다 — 그러면 이 도구를 부르는 **롤백 게이트(B10)가
        #   통째로 실패**한다. 실제로 그렇게 죽어 있었고, B10 이 오래
        #   `UNMEASURED`(다른 세션 오염) 였던 탓에 아무도 못 봤다.
        #   핀이 없는 것은 고장이 아니라 **사실**이다 — 그렇게 적는다.
        print(f"  {r:22} pin={(p or '(핀 없음)'):12} ref={','.join(refs)}")

    if args.check:
        distinct = {p for p in pins.values() if p}
        distinct_refs = {x for v in wf_refs.values() for x in v}
        if len(distinct) > 1:
            print(f"\n[bump_ec_pin] ✗ pin lockstep 위반: {distinct} — bump 필요")
            return 1
        skew = distinct_refs - distinct
        if skew:
            print(f"\n[bump_ec_pin] ✗ ssot-drift ref 가 pin 과 skew: ref={distinct_refs} vs pin={distinct}")
            print("  → CI 가 옛 스키마로 --check 를 돌려 DRIFT 오탐한다. bump 로 동반 갱신할 것.")
            return 1
        # ⚠ 여기까지는 **핀끼리** 같은지만 봤다. 그게 사각이었다 —
        #   2026-08-16 실측: 전 소비자 pin=v0.3.39 로 일치해 이 검사가 ✓ 를 냈는데,
        #   커밋된 생성상수는 master(스키마 33 종) 해시였고 v0.3.39 엔 그 스키마가
        #   없다. CI 가 pin 대로 checkout 하면 전 소비자 DRIFT.
        #   **핀이 서로 같은 것과 핀이 옳은 것은 다른 질문이다.**
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _pin_hash_check import check as _pin_hash_ok

        if _pin_hash_ok(CONTRACTS_ROOT, PROJECTS, CONSUMERS,
                        next(iter(distinct)) if len(distinct) == 1 else None):
            return 1
        print("\n[bump_ec_pin] ✓ pin lockstep OK (ssot-drift ref + 태그↔해시 재현)")
        return 0

    if not args.target:
        print("\n[bump_ec_pin] target 태그 필요 (예: python bump_ec_pin.py v0.3.6)")
        return 2
    if not re.fullmatch(r"v[0-9][\w.\-]*", args.target):
        print(f"[bump_ec_pin] 태그 형식 오류: {args.target}")
        return 2

    print(f"\n[bump_ec_pin] → {args.target} 일괄 bump")
    changed = bump_pins(args.target)
    print(f"  pyproject pin 변경: {changed or '없음(이미 동일)'}")
    changed_wf = bump_wf_refs(args.target)
    print(f"  ssot-drift ref 변경: {changed_wf or '없음(이미 동일)'}")

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
