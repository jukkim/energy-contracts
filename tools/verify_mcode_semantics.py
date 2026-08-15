#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M-code 의미가 **전 저장소에서** 정본과 같은가 — 교차 저장소 게이트.

## 왜 이 도구가 있는가

2026-06-22 에 M-code 역매핑 사고를 정정했다(3 repo). 그런데 **2026-08-15 에 또
어긋났다** — `building-energy-3d-lab` 에서:

    M03  Lab "야간냉방차단"     ↔ 정본 냉동기·보일러 대수 제어
    M07  Lab "냉방설정온도조정"  ↔ 정본 CO2 수요제어환기
    M09  Lab "야간조명차단"     ↔ 정본 피크 전 프리쿨링
    M12  Lab "ESS방전"        ↔ 정본 통합+PMV0.5

재발 원인은 분명하다 — **그때 회귀 가드를 `agentleague` 한 곳에만 넣었다.**
가드가 한 저장소에만 있으면 형제는 다시 어긋난다. 그래서 이번엔 **정본 저장소에 두고
어느 저장소든 훑을 수 있게** 만든다.

## 정본 (시뮬 데이터 기준)

    energy-contracts/energy_contracts/schemas/ems_strategies.json → default.strategies

근거는 시뮬레이션이다 — 352k 시뮬로 학습한 `reverse` 의 `M_LABELS` 가 M00~M15 로
이 표와 일치한다.

⚠ **`8.simulation/ems_simulation/config/ems_strategies.yaml` 은 정본이 아니다.**
`m0`~`m8` 의 **폐기된 세대**다(`m0=NightCycle` vs 정본 `M06=NightCycle`).

## 두 형태를 다르게 본다

    선언형  "M07": "조명 제어"      → **정본 낱말이 하나라도 있어야** 한다
    산문형  M07(조명 제어) 를 켠다  → **남의 전략 낱말**이 붙었을 때만 잡는다

⚠ 이 구분이 없으면 `"M07": "냉방설정온도조정"` 처럼 **남의 낱말이 없는 오매핑**을
영영 못 잡는다. 실제로 첫 판본이 알려진 4 건을 0 건으로 통과시켰다.

## 검사하지 않는 것

- **산출물**(`outputs/`·`results/`·`evidence/`…) — 과거 실행 결과를 손으로 고치면
  수정이 아니라 **결과 변조**다. 라벨이 틀렸으면 생성기를 고친다.
- **ADR** — 결정 이력이다. 과거 표기 인용이 본질이라 고치면 ADR 이 거짓이 된다.
- **이력 인용 줄**("구 체계"·"오기"·"폐기" 등이 있는 줄)
- **나열 문장**(`M01(ScheduleOpt · M06=NightCycle)`) — 이름 표기가 아니다
- **게이트 자기 자신**

사용:
    python tools/verify_mcode_semantics.py                  # 등록된 전 저장소
    python tools/verify_mcode_semantics.py --repo <경로>     # 한 저장소만
    python tools/verify_mcode_semantics.py --strict         # 위반 시 exit 1
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve()
EC_ROOT = HERE.parents[1]
WORKSPACE = EC_ROOT.parents[1]

CANON_PATH = EC_ROOT / "energy_contracts" / "schemas" / "ems_strategies.json"

#: M-code 이름을 적을 수 있는 저장소. **새 저장소가 생기면 여기 한 줄** 추가한다.
REPOS = [
    "projects/building-energy-3d",
    "projects/building-energy-3d-lab",
    "projects/energy-decision-studio",
    "projects/energy-decision-canvas",
    "projects/agentleague",
    "projects/gridbridge",
    "projects/mgcc",
    "projects/ui_services",
    "projects/bems-console",
    "projects/energy-contracts",
    "8.simulation/ems_transformer",
    "8.simulation/reverse",
    "공모전/2026-04-24_AI챔피언_전국민AI경진대회",
]

SKIP_PARTS = {
    ".git", "node_modules", "__pycache__", "build", "dist", ".next",
    ".venv", "venv", "archive", "_archive", "scratch", "site-packages",
    ".mypy_cache", ".pytest_cache",
    # 시험 자신이 **일부러 심은 오매핑 표본**을 들고 있다(뮤테이션 대조군).
    # 그걸 위반으로 세면 게이트가 자기 시험을 못 갖는다.
    "tests", "test",
    # 산출물 — 고치면 결과 변조다
    "outputs", "output", "results", "evidence", "captures_raw",
    "logs", "checkpoints", "fixtures", "__snapshots__",
    # ADR — 결정 이력이다
    "adr",
}

SCAN_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yaml", ".yml"}

CODE = r"M(?:0\d|1\d|2[0-2])"

#: 선언형 — "이 코드의 이름은 이것" 이라고 못박은 형태
DECLARED = re.compile(r"[\"']?(" + CODE + r")[\"']?\s*[:=]\s*[\"']([^\"'\n]{2,40})[\"']")

#: 산문형 — 문장 안에 곁들인 형태
PROSE = re.compile(r"\b(" + CODE + r")\b\s*(?:\(|:\s|=\s|\s—\s|\s-\s)"
                   r"([^)\"'\n,;{}\[\]]{2,40})")

#: 여러 코드를 나열한 문장은 이름 표기가 아니다
ENUMERATION = re.compile(CODE)

#: 과거 표기를 **인용**하는 줄 — 고치면 이력이 거짓이 된다
HISTORICAL = re.compile(
    r"구\s*체계|이전\s*체계|폐기|오기|deprecated|legacy|과거|였음|였다|"
    r"이전에는|바뀌기\s*전|→\s*" + CODE)

#: 정본 이름의 **핵심 낱말**. 표기는 저장소마다 달라도 되지만(예 "DCV" vs
#  "CO2 수요제어환기"), 선언형은 이 중 하나는 있어야 한다.
SEMANTIC_KEYS = {
    "M00": ["baseline", "기준", "고정 설정온도", "setback", "셋백"],
    "M01": ["scheduleopt", "최적 기동", "최적기동", "optimalstart", "기동·정지", "기동정지"],
    "M02": ["economizer", "이코노마이저", "외기", "무료냉방", "외기냉방"],
    "M03": ["staging", "대수 제어", "대수제어", "냉동기", "보일러"],
    "M04": ["pmv_strict", "pmv ±0.5", "pmv±0.5", "pmv 0.5", "pmv0.5"],
    "M05": ["pmv_relaxed", "pmv ±0.7", "pmv±0.7", "pmv 0.7", "pmv0.7"],
    "M06": ["nightcycle", "야간 순환", "야간순환"],
    "M07": ["dcv", "수요제어환기", "co2", "환기"],
    "M08": ["heatrecovery", "전열교환", "erv", "폐열", "열회수"],
    "M09": ["precooling", "preheating", "프리쿨링", "프리히팅", "예냉", "예열"],
    "M10": ["demandresponse", "수요반응", "부하 제한", "부하제한", "피크 전력", "피크전력"],
    "M11": ["combined_ems", "통합 ems", "통합ems"],
    "M12": ["combined_pmv05", "통합+pmv0.5", "pmv0.5", "pmv 0.5"],
    "M13": ["combined_pmv07", "통합+pmv0.7", "pmv0.7", "pmv 0.7"],
    "M14": ["combined_full", "통합 완전", "통합완전"],
    "M15": ["combined_premium", "통합 프리미엄", "통합프리미엄"],
    "M16": ["dr_nightsetback", "야간 셋백", "야간셋백", "셋백"],
    "M17": ["lightingcontrol", "조명"],
    "M18": ["esspeakshaving", "ess", "피크셰이빙"],
    "M19": ["dr_integrated", "dr 통합", "통합 최적화", "통합최적화"],
    "M20": ["dr_emergencycurtail", "긴급 감축", "긴급감축"],
    "M21": ["thermalstorage", "빙축열", "수축열", "열저장"],
    "M22": ["pv_selfconsumption", "태양광", "자가소비", "pv"],
}

#: 붙으면 **다른 전략의 낱말**임이 분명한 것 — 산문형 적발용
FOREIGN = {
    "조명": {"M17", "M19", "M20"},
    "ess": {"M18", "M19", "M20"},
    "환기": {"M07", "M14", "M15"},
    "dcv": {"M07", "M14", "M15"},
    "프리쿨링": {"M09", "M20"},
    "예냉": {"M09", "M20"},
    "이코노마이저": {"M02", "M11", "M12", "M13", "M14", "M15", "M19", "M20"},
    "외기냉방": {"M02", "M11", "M12", "M13", "M14", "M15", "M19", "M20"},
    "야간순환": {"M06", "M14", "M15"},
    "야간 순환": {"M06", "M14", "M15"},
    "대수제어": {"M03", "M11", "M12", "M13", "M14", "M15"},
    "대수 제어": {"M03", "M11", "M12", "M13", "M14", "M15"},
    "빙축열": {"M21"},
    "태양광": {"M22"},
}


def canon() -> dict:
    return json.loads(CANON_PATH.read_text(encoding="utf-8"))["default"]["strategies"]


def iter_files(repo: Path):
    for p in repo.rglob("*"):
        if p.suffix.lower() not in SCAN_EXT or not p.is_file():
            continue
        if SKIP_PARTS & {x.lower() for x in p.relative_to(repo).parts}:
            continue
        if p.resolve() == HERE:
            continue          # 게이트 자기 자신의 설명 예시
        yield p


def _skip(label: str) -> bool:
    low = label.strip().lower()
    if not low or low in {"true", "false", "null", "none"}:
        return True
    if ENUMERATION.search(label):
        return True
    return bool(re.fullmatch(r"[\d\s.,%_\-/]+", low))


#: 남의 낱말이 **더 긴 단어 안에** 우연히 들어간 경우. 한글은 낱말 경계가 없어
#  부분 문자열 매칭이 오탐을 만든다 — 실제로 "전열교환기" 의 "교환기" 를 '환기' 로
#  잡았다. 이런 걸 위반으로 세면 멀쩡한 설명을 고치게 된다.
FALSE_HOSTS = {
    "환기": ["교환기", "교환器", "열교환"],
    "예냉": ["예열·예냉", "예냉·예열", "예열/예냉", "예냉/예열"],
    "ess": ["process", "assess", "less", "press", "necess"],
    "pv": ["pvc"],
}


def check_foreign(code: str, label: str) -> str | None:
    """남의 전략 낱말이 붙었는가 — 오매핑의 확실한 신호."""
    if _skip(label):
        return None
    low = label.strip().lower()
    for word, owners in FOREIGN.items():
        if word not in low or code in owners:
            continue
        # 더 긴 단어 안에 우연히 들어간 것이면 넘어간다
        if any(h in low for h in FALSE_HOSTS.get(word, [])):
            continue
        return f"'{word}' 는 {'/'.join(sorted(owners))} 의 의미다"
    return None


#: 이 길이를 넘으면 **이름표가 아니라 설명문**으로 본다. 설명은 표현이 자유로우므로
#  정본 낱말을 요구하지 않는다 — `M09: "피크 전에 미리 냉방해 부하를 분산"` 은
#  정확한 설명인데 '프리쿨링' 이 없다고 잡으면 멀쩡한 문장을 고치게 된다.
DESCRIPTION_LEN = 16


def check_declared(code: str, label: str, st: dict) -> str | None:
    """선언형은 **정본 낱말이 하나라도 있어야** 한다(짧은 이름표일 때만)."""
    if _skip(label):
        return None
    fk = check_foreign(code, label)
    if fk:
        return fk
    if len(label.strip()) > DESCRIPTION_LEN:
        return None                 # 설명문 — 남의 낱말만 봤고 통과했다
    low = label.strip().lower()
    if any(k in low for k in SEMANTIC_KEYS.get(code, [])):
        return None
    e = st.get(code) or {}
    for nm in (e.get("name_en", ""), e.get("name_kr", "")):
        if nm and nm.lower() in low:
            return None
    return (f"정본은 '{e.get('name_kr', '?')}'({e.get('name_en', '?')}) 인데 "
            f"어느 낱말도 안 맞는다")


def scan(repo: Path, st: dict) -> list[tuple[str, int, str, str, str]]:
    out: list[tuple[str, int, str, str, str]] = []
    for p in iter_files(repo):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # ⚠ 빠른 걸러내기. 부분 문자열("M0")로 쓰면 SSOT pre-commit 이 이를
        #   "구 전략 코드 M0~M8 단독" 으로 잡는다(정당한 차단이다) → 정규식으로.
        if not re.search(CODE, text):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if HISTORICAL.search(line):
                continue
            seen = set()
            for m in DECLARED.finditer(line):
                code, label = m.group(1), m.group(2)
                seen.add((code, label))
                why = check_declared(code, label, st)
                if why:
                    out.append((str(p.relative_to(repo)), i, code, label.strip(), why))
            for m in PROSE.finditer(line):
                code, label = m.group(1), m.group(2)
                if (code, label) in seen:
                    continue
                why = check_foreign(code, label)
                if why:
                    out.append((str(p.relative_to(repo)), i, code, label.strip(), why))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M-code 의미 교차 저장소 게이트")
    ap.add_argument("--repo", help="한 저장소만 검사(경로)")
    ap.add_argument("--strict", action="store_true", help="위반 시 exit 1")
    ap.add_argument("--limit", type=int, default=20, help="저장소당 표시 건수")
    a = ap.parse_args(argv)

    st = canon()
    print("=" * 74)
    print(f"M-code 의미 게이트 — 정본 {len(st)}종 ({CANON_PATH.name})")
    print("  ⚠ ems_simulation/config/ems_strategies.yaml 은 폐기 세대(m0~m8). 정본 아님.")
    print("=" * 74)

    repos = [Path(a.repo)] if a.repo else [WORKSPACE / r for r in REPOS]
    total = scanned = 0
    for repo in repos:
        if not repo.is_dir():
            print(f"  ⏭ 없음: {repo}")
            continue
        scanned += 1
        hits = scan(repo, st)
        label = repo.name or str(repo)
        if not hits:
            print(f"  ✅ {label}")
            continue
        print(f"  ⛔ {label} — {len(hits)}건")
        for rel, ln, code, lab, why in hits[:a.limit]:
            print(f"       {rel}:{ln}  {code}({lab})  ← {why}")
        if len(hits) > a.limit:
            print(f"       … 외 {len(hits) - a.limit}건")
        total += len(hits)

    print("-" * 74)
    if scanned == 0:
        print("⛔ 검사한 저장소가 0 개다 — 경로가 어긋났다(가드가 공허하다).")
        return 1
    if total:
        print(f"⛔ 오매핑 {total}건. 정본 = `{CANON_PATH.name}` 의 `default.strategies`")
        return 1 if a.strict else 0
    print(f"✅ 저장소 {scanned}개 — 오매핑 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
