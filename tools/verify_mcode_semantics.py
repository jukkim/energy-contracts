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
    "projects/edge-agent",
    "projects/energy-contracts",
    "8.simulation/ems_transformer",
    "8.simulation/reverse",
    "공모전/2026-04-24_AI챔피언_전국민AI경진대회",
    # ⚠ 아래 셋은 **등록만 안 돼 있었다.** 게이트가 못 본 게 아니라 안 봤다.
    #   `reverse-ems` 는 `8.simulation/reverse` 의 통째 stale 사본이라(junction 아님)
    #   여기서 표를 재생성하면 **고친 라벨이 되돌아온다**(사냥꾼 F4).
    #   ⚠ 단 이 저장소는 GitHub 에서 **archived(동결)** 다 — push 가 403 으로 막힌다.
    #     그건 고장이 아니라 의도다. 로컬 정정만 두고 원격은 건드리지 않는다.
    #     (2026-08-15 확인: isArchived=true, pushedAt 2026-07-26)
    "projects/reverse-ems",
    "8.simulation/ems_simulation",
    "8.simulation/sim_campaign_2026",
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

#: ⚠ `.txt`·`.tex`·`.html` 이 빠져 있어 **시스템 프롬프트·논문 본문·제어 화면**을 통째로
#  못 봤다(사냥꾼 2026-08-15 F3/F8). 라벨은 확장자를 가리지 않는다.
#  `.jsonl` 은 **크기 상한과 함께** 본다 — 학습 코퍼스가 수십 MB 라 전량 정규식은 못 건다.
SCAN_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yaml", ".yml",
            ".txt", ".tex", ".html", ".jsonl"}

#: `.jsonl` 만 적용하는 상한(바이트). 넘으면 건너뛰되 **조용히 넘기지 않는다**(§iter_files).
JSONL_MAX_BYTES = 8 * 1024 * 1024

#: 큰 `.jsonl` 에서 볼 **앞부분 표본 줄 수.** 전량은 너무 느려 아무도 안 돌린다.
JSONL_SAMPLE_LINES = 3000

#: ⚠ 예전 주석은 "`m07` 도 본다" 고 적혀 있었지만 **문자군에 소문자가 없었다**.
#   심기 시험에서 적발해 열어 봤더니 — **소문자는 다른 네임스페이스였다.**
#   `m07`·`m12` 는 폐기된 시뮬 m-코드(m→E→M 2단 매핑)라 그 체계 안에서는 맞다
#   (`m12→E5(DCV)`·`m07→E1(NightCycle)`). M-정본 잣대로 재면 멀쩡한 기록이 위반이 된다.
#   → **대문자(+전각)만 본다.** 주석이 고쳤다고 말해도 코드가 안 고쳤으면 안 고친 것이고,
#     반대로 코드를 열었는데 오탐이 나오면 그건 열지 말아야 할 문이었다.
CODE = r"[MＭ]\s?(?:[0０][0-9０-９]|[1１][0-9０-９]|[2２][0-2０-２])"

#: 선언형 — "이 코드의 이름은 이것" 이라고 못박은 형태
#: ⚠ 상한이 40 이라 **44 자 라벨은 남의 낱말 검사조차 안 돌았다**(사냥꾼 실증).
DECLARED = re.compile(r"[\"']?(" + CODE + r")[\"']?\s*[:=]\s*[\"']([^\"'\n]{2,120})[\"']")

#: 배열값 선언 — `"M09": ["야간 조명 차단해줘", …]`
#: ⚠ `DECLARED` 는 `[:=]` 뒤에 **바로** 따옴표를 요구해서 `[` 가 끼면 불발했다.
#   그 사각지대에 LoRA 학습쌍 생성기(`STRATEGY_NL`)가 통째로 들어 있었다 — 23 종 중
#   22 종이 틀렸는데 게이트는 초록이었다(사냥꾼 F1).
ARRAY_DECLARED = re.compile(
    r"[\"']?(" + CODE + r")[\"']?\s*:\s*\[\s*[\"']([^\"'\n]{2,120})[\"']")

#: 파이프 표 — `| M07 | NightCycle | 야간 순환 |`  ·  LaTeX — `M07 & NightCycle &`
#: ⚠ 구분자가 `|`/`&` 라 `DECLARED`·`PROSE` 둘 다 미매치였다. 논문 표·특허 초안
#   26 곳이 이 구멍에 있었다(사냥꾼 F3).
#: ⚠ 앞 구분자를 **필수**로 두면 LaTeX **첫 열**을 통째로 놓친다 — `M07 & DCV & 0.855 \\`
#   는 코드 앞에 `&` 가 없다. 논문 표가 정확히 그 형태라, 심기 시험 6 건 중 이것만
#   미검출이었다(2026-08-15). 줄머리·여백 뒤도 허용한다.
TABLE = re.compile(r"(?:^|[|&])\s*(" + CODE + r")\s*[|&]\s*([^|&\n]{2,120}?)\s*(?:[|&]|$)",
                   re.M)

#: 산문형 — 문장 안에 곁들인 형태
#: ⚠ `=\s` 가 **등호 뒤 공백**을 요구해서 `M03=night-HVAC-off` 를 통째로 놓쳤다.
#   2026-08-15 원 4 건의 **영문판**이 `gen_ops.py` 영어 설명에 그대로 살아 있었는데
#   (`M07=setpoint-adjust, M09=night-lighting-off …`) 전 범위 게이트는 0 건이었다.
#   영어를 안 본 게 아니라 **그 형태를 안 봤다.** 공백을 선택적으로 바꾼다.
#: ⚠ 공백을 선택으로 바꾸자 이번엔 **범위 서술**이 걸렸다 —
#   `M00~M20=시뮬 EMS(...)` 의 **범위 끝**을 라벨로 읽는다. 범위 표식(`~`·`-`·`–`)
#   바로 뒤의 코드는 이름을 받는 자리가 아니다.
PROSE = re.compile(r"(?<![~\-–—])\b(" + CODE + r")\b\s*(?:\(|:\s|=\s?|\s—\s|\s-\s)"
                   r"([^)\"'\n,;{}\[\]]{2,40})")

#: 여러 코드를 나열한 문장은 이름 표기가 아니다
ENUMERATION = re.compile(CODE)

#: 과거 표기를 **인용**하는 줄 — 고치면 이력이 거짓이 된다
HISTORICAL = re.compile(
    r"구\s*체계|구\s*의미|이전\s*체계|이전\s*의미|오염|contamination|"
    r"폐기|오기|deprecated|legacy|과거|였음|였다|"
    r"이전에는|바뀌기\s*전|구\s*M-?code|오기였|잔존|hits\(|비정본|드리프트|drift|불일치|잘못|정정|틀렸|→\s*" + CODE)

#: 정본 이름의 **핵심 낱말**. 표기는 저장소마다 달라도 되지만(예 "DCV" vs
#  "CO2 수요제어환기"), 선언형은 이 중 하나는 있어야 한다.
#  ⚠ 실제 저장소에서 쓰는 표현을 **전수로 훑어 보강**했다(2026-08-15). 정본 문구만
#     넣어 두면 "칠러 대수제어"·"스케줄 최적화" 처럼 **의미는 맞는데 표현만 다른** 것을
#     위반으로 잡아, 멀쩡한 문구를 고치게 된다.
SEMANTIC_KEYS = {
    "M00": ["baseline", "기준", "무전략", "고정 설정온도", "setback", "셋백"],
    "M01": ["scheduleopt", "기동", "최적 기동", "최적기동", "optimalstart", "기동·정지",
            "기동정지", "스케줄", "schedule", "schedopt", "가동 스케줄", "운전 스케줄", "시간 최적"],
    "M02": ["economizer", "이코노마이저", "외기", "무료냉방", "외기냉방", "엔탈피"],
    "M03": ["staging", "stg", "대수", "대수 제어", "대수제어", "냉동기", "보일러", "칠러", "chiller"],
    "M04": ["pmv_strict", "pmv", "설정온도", "설정 온도", "온도 조정", "쾌적", "엄격", "strict"],
    "M05": ["pmv_relaxed", "pmv", "설정온도", "설정 온도", "온도 조정", "완화", "쾌적", "relaxed"],
    "M06": ["nightcycle", "night cycle", "night-cycle", "야간", "야간 순환", "야간순환", "야간 사이클", "야간운전", "간헐운전", "간헐 운전"],
    "M07": ["dcv", "수요제어", "수요제어환기", "수요제어 환기", "co2", "환기"],
    "M08": ["heatrecovery", "전열", "전열교환", "erv", "폐열", "열회수"],
    "M09": ["precooling", "pre-cooling", "pre cooling", "preheating", "선행냉방", "선행 냉방", "프리쿨", "프리히팅", "프리히트", "예냉", "예열",
            "미리 냉방", "선제 냉방", "사전 냉방", "선제냉방", "사전냉방"],
    "M10": ["demandresponse", "수요반응", "부하 제한", "부하제한", "피크 전력",
            "피크전력", "dr", "수요 반응"],
    "M11": ["combined_ems", "통합", "복합", "결합", "combined"],
    "M12": ["combined_pmv05", "통합", "복합", "결합", "combined", "pmv", "엄격", "엄격쾌적", "엄격 쾌적"],
    "M13": ["combined_pmv07", "통합", "복합", "결합", "combined", "pmv", "완화", "완화쾌적", "완화 쾌적"],
    "M14": ["combined_full", "통합", "복합", "결합", "combined", "완전", "풀", "full", "전부하"],
    "M15": ["combined_premium", "통합", "복합", "결합", "combined", "프리미엄", "premium"],
    "M16": ["dr_nightsetback", "dr", "야간 셋백", "야간셋백", "셋백", "setback"],
    "M17": ["lightingcontrol", "조명", "디밍", "lighting"],
    "M18": ["esspeakshaving", "ess", "피크셰이빙", "피크 셰이빙", "peak shaving"],
    "M19": ["dr_integrated", "dr", "dr 통합", "통합 최적화", "통합최적화", "통합"],
    "M20": ["dr_emergencycurtail", "dr", "긴급 감축", "긴급감축", "긴급", "curtail"],
    "M21": ["thermalstorage", "빙축열", "수축열", "열저장", "축열"],
    "M22": ["pv_selfconsumption", "태양광", "자가소비", "pv", "발전"],
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
    # ⚠ 영문 전략명이 통째로 빠져 있었다 — 논문·특허·LaTeX 는 **영문으로 쓴다**.
    #   `| M07 | NightCycle |` 26 곳이 이 누락 때문에 초록이었다(사냥꾼 F3).
    "nightcycle": {"M06", "M14", "M15"},
    "night cycle": {"M06", "M14", "M15"},
    "night-cycle": {"M06", "M14", "M15"},
    "economizer": {"M02", "M11", "M12", "M13", "M14", "M15", "M19", "M20"},
    "lighting": {"M17", "M19", "M20"},
    "precooling": {"M09", "M20"},
    "pre-cooling": {"M09", "M20"},
    "staging": {"M03", "M11", "M12", "M13", "M14", "M15"},
    "optimalstart": {"M01", "M11", "M12", "M13", "M14", "M15"},
    "optimal start": {"M01", "M11", "M12", "M13", "M14", "M15"},
    "heatrecovery": {"M08", "M14", "M15"},
    "heat recovery": {"M08", "M14", "M15"},
    "thermalstorage": {"M21"},
    "peak shaving": {"M18", "M19", "M20"},
    "피크셰이빙": {"M18", "M19", "M20"},
    # ⚠ 영문 `night` 가 없어 `M03=night-HVAC-off` 를 놓쳤다(심기 시험 적발).
    #   소유자에 M09 를 넣는다 — **프리쿨링은 실제로 야간에 한다.** 안 넣으면
    #   `M09(pre-cooling at night)` 라는 정확한 서술을 위반이라 부른다.
    "night": {"M00", "M06", "M09", "M14", "M15", "M16"},
    # ⚠ 산문형을 **남의 낱말로만** 판정하려면 그 사전이 실제 오매핑을 덮어야 한다.
    #   2026-08-15 원 4 건 중 `M07(냉방설정온도조정)`·`M03(야간냉방차단)` 두 건이
    #   여기 없어서 통과했다 — 남의 어휘가 안 섞였던 게 아니라 **사전이 얕았다**.
    "설정온도": {"M00", "M04", "M05", "M12", "M13", "M14", "M15", "M16", "M19"},
    "설정 온도": {"M00", "M04", "M05", "M12", "M13", "M14", "M15", "M16", "M19"},
    "야간": {"M00", "M06", "M14", "M15", "M16"},
    "방전": {"M18", "M19", "M20", "M22"},
    "충전": {"M18", "M19", "M20", "M22"},
    "축열": {"M21"},
    "디밍": {"M17", "M19", "M20"},
}


#: **전략 어휘 사전** — "여기가 이름을 말하는 자리인가" 를 가르는 관문.
#
#  산문형 괄호는 **부연이 기본값**이다: `M15(16개)` · `M09(prob 0.9992)` ·
#  `M08(n=5)` · `M20(slow-path 제외)` · `M00(제어 없음)`. 이걸 이름표로 보고 "정본
#  낱말이 없다" 고 잡으면 **10,798 건**이 나온다(실측). 그중 진짜는 한 줌이다 —
#  목록이 길면 사람이 안 보고, 안 보면 안 고친다.
#
#  그래서 **라벨이 어떤 전략의 어휘를 담고 있을 때만** 이름표로 본다.
#  `M07(냉방설정온도조정)` 은 '설정온도' 가 있으니 이름을 말하는 자리다 → 판정한다.
#  `M07(**92.7%**)` 은 어떤 전략 어휘도 없으니 부연이다 → 넘어간다.
_VOCAB_EXTRA = [
    "냉방", "난방", "야간", "조명", "환기", "설정온도", "설정 온도", "기동", "정지",
    "대수", "축열", "태양광", "예냉", "예열", "셋백", "디밍", "피크", "충전", "방전",
    "차단", "쾌적", "외기", "열회수", "수요반응", "수요 반응", "감축", "스테이징",
    "night", "hvac",
]


def _names_vocab() -> set[str]:
    v = {w.lower() for ws in SEMANTIC_KEYS.values() for w in ws}
    v |= {w.lower() for w in FOREIGN}
    v |= {w.lower() for w in _VOCAB_EXTRA}
    return v


VOCAB = _names_vocab()


def is_name_slot(label: str) -> bool:
    """이 라벨이 **전략 이름을 말하는 자리**인가 (부연 괄호가 아니라)."""
    low = label.strip().lower()
    return any(w in low for w in VOCAB)


#: **학습 코퍼스**는 코드가 아니라 데이터다. 라벨이 틀렸으면 손으로 고칠 게 아니라
#  **재증류**한다 — 과거 생성물을 손편집하면 그건 수정이 아니라 데이터 변조다.
#  그래서 따로 세고 따로 보고한다. **감추지는 않는다**(안 본 게 아니라 다르게 다룬다).
#
#  ⚠ 단 **라이브 학습 입력은 예외**다. 지금 학습에 들어가는 코퍼스가 오염되면 그건
#    모델의 행동에 닿으므로 코드와 같은 등급으로 실패시킨다.
DATA_CORPUS_HINTS = ("debate_dataset", "lora2_", "/data/training/", "\\data\\training\\",
                     "inference_w5", "eval_v2.0", "corpus", "/datasets/", "cot_")
LIVE_CORPUS_HINTS = ("lora2_corpus_v4_1_refined",)


def is_data_corpus(rel: str) -> bool:
    low = rel.replace("/", "\\").lower()
    if any(h.replace("/", "\\") in low for h in LIVE_CORPUS_HINTS):
        return False                      # 라이브 = 코드 등급
    return low.endswith(".jsonl") and any(
        h.replace("/", "\\") in low for h in DATA_CORPUS_HINTS)


#: **미해결 충돌 경로.** `reverse` 논문·특허는 7 번째 비트를 NightCycle 로 서술하는데
#  정본은 M07=DCV 다. 학습 매니페스트에 **E5 가 아예 없어**(E0·E1·E3·E4·E6~E13만)
#  `E5→M07` 매핑이 죽은 것으로 보이지만, 실측 전에는 어느 쪽도 단정할 수 없다.
#  라벨만 정본에 맞추면 논문의 물리 서술·외부 검증 해석이 통째로 어긋난다
#  (실제로 한 번 그렇게 만들었다가 되돌렸다).
#  → **위반으로 세지 않되 감추지도 않는다.** 매 실행마다 이 문서로 안내한다.
PAPER_CONFLICT_PATHS = ("reverse/paper", "paper/latex", "paper/tables",
                        "paper/manuscript", "patent_draft", "_patent_v2",
                        "mcode_bit7_identity_conflict", "session_summary_20260511")
PAPER_CONFLICT_DOC = "8.simulation/reverse/docs/MCODE_BIT7_IDENTITY_CONFLICT_2026-08-15.md"


#: **확정된 vintage 예외.** `reverse` 계열에서 `M07 = NightCycle` 은 오매핑이 아니라
#  **2026-05-13 이전 매핑의 정확한 이름**이다(실측 확정 — 논문의 7비트 조합
#  `{M00..M05, M07}`(M06 부재)은 `E1→M07` 시절에만 재현되고, 현재 매핑으로 20k 캐시를
#  재구성하면 M07 표본이 0 이다. 표본 0 인 비트가 F1 0.855 를 낼 수 없다).
#
#  ⚠ 경로가 아니라 **이 짝 하나만** 면제한다. 경로로 막으면 그 안의 **다른** 오매핑까지
#    같이 눈감게 된다 — 이번 세션이 통째로 그 교훈이다.
VINTAGE_REPOS = ("reverse", "reverse-ems")
#  vintage 는 **두 코드가 맞물린 짝**이다 — 그 시절엔 M06↔DCV, M07↔NightCycle 이었다.
VINTAGE_PAIRS = {
    "M07": ("nightcycle", "night cycle", "night-cycle", "야간 순환", "야간순환"),
    "M06": ("dcv", "수요제어환기", "수요제어 환기", "co2 농도"),
}


def is_vintage_pair(scope: str, code: str, label: str) -> bool:
    """`scope` = 저장소 이름 **또는** 파일 경로. 어느 쪽이든 `reverse` 계열인지 본다.

    ⚠ 저장소 이름만 보면 `--repo 8.simulation --files reverse/...` 처럼
      **상위 저장소에서 하위 경로를 지목**할 때 범위를 놓친다(훅이 자기 문서를
      위반이라 막았다). 경로의 **디렉터리 성분**으로도 판정한다.
    """
    parts = {x.lower() for x in scope.replace(chr(92), "/").split("/") if x}
    if not (parts & set(VINTAGE_REPOS)):
        return False
    words = VINTAGE_PAIRS.get(code)
    if not words:
        return False
    low = label.lower()
    return any(w in low for w in words)


def is_paper_conflict(rel: str) -> bool:
    """⛔ **더는 쓰지 않는다.** 경로로 면제했더니 그 안의 **다른** 오매핑까지 가렸다 —
    `patent_draft_v2.md` 에 `| M03 | Economizer |` 를 심었는데 안 잡혔다(실증).
    면제는 **사안(vintage 짝)** 으로만 건다. 이 함수는 항상 False 다."""
    return False


def canon() -> dict:
    return json.loads(CANON_PATH.read_text(encoding="utf-8"))["default"]["strategies"]


#: 이름으로 알 수 있는 **산출물 파일**. 디렉터리로 못 거른 것들.
#  모델이 생성한 답변이 들어 있어, 손으로 고치면 **평가 기록 변조**다.
#  라벨이 틀렸으면 고칠 곳은 파일이 아니라 **그라운딩/코퍼스**다.
ARTIFACT_STEMS = ("scorecard", "eval_result", "run_", "report_", "_snapshot",
                  "predictions", "answers", "qa_live")


#: `.jsonl` 크기 상한에 걸려 **안 본** 파일. 조용히 넘기면 그게 다음 사각지대가 된다.
SKIPPED_TOO_BIG: list[str] = []


def iter_files(repo: Path):
    for p in repo.rglob("*"):
        if p.suffix.lower() not in SCAN_EXT or not p.is_file():
            continue
        if p.suffix.lower() == ".json" and any(s in p.stem.lower() for s in ARTIFACT_STEMS):
            continue
        # ⚠ `scratch_` 접두 = **파생 작업 파일**이다. 디렉터리 `scratch/` 는 이미 걸렀는데
        #   접두만 붙은 파일은 안 걸러져, 폐기된 초안의 추출 텍스트가 영구히 잡혔다.
        #   (2026-08-15: `본선/임시본/scratch_extract_v12.txt` — **최종 제출본은 깨끗함을
        #    hwpx 원본에서 직접 확인**했다. 걸린 건 superseded 초안의 파생물이다.)
        if p.stem.lower().startswith("scratch_"):
            continue
        # ⚠ **더는 건너뛰지 않는다.** 큰 `.jsonl` 은 `scan_file` 이 스트리밍으로 본다.
        #   기록만 남긴다 — 어떤 파일이 그 경로를 탔는지는 알아야 한다.
        if p.suffix.lower() == ".jsonl":
            try:
                if p.stat().st_size > JSONL_MAX_BYTES:
                    SKIPPED_TOO_BIG.append(str(p))
            except OSError:
                continue
        if SKIP_PARTS & {x.lower() for x in p.relative_to(repo).parts}:
            continue
        if p.resolve() == HERE:
            continue          # 게이트 자기 자신의 설명 예시
        yield p


#: 다른 코드 체계로의 **대응표**(예: `"M00": "E0"`). 이름이 아니라 매핑이다.
#  `build_rvk_metadata.py` 의 `M_TO_E` 가 그렇다 — 원 시뮬 실험 코드와의 대응.
#: ⚠ `PMV05`·`PMV07`·`PV1` 을 면제하던 구멍이 있었다 — 하필 M04↔M05 를 가르는 유일한
#   표기라 그 혼동을 구조적으로 못 봤다(사냥꾼 실증). **의미 있는 접두는 이름으로 본다.**
_MEANINGFUL_PREFIX = re.compile(r"^(?:pmv|pv|ess|dr|dcv|erv|cop)", re.I)
CODE_ALIAS = re.compile(r"^(?:[A-Za-z]{1,3}\d{1,3}|\d{1,3})$")


def _skip(label: str) -> bool:
    low = label.strip().lower()
    if not low or low in {"true", "false", "null", "none"}:
        return True
    s = label.strip()
    if CODE_ALIAS.fullmatch(s) and not _MEANINGFUL_PREFIX.match(s):
        return True                 # 코드 대응표지 이름이 아니다
    if ENUMERATION.search(label):
        return True
    if re.fullmatch(r"[\d\s.,%_\-/±]+", low):
        return True
    # `SCHEDULE(20)` · `DR_DISPATCH(10)` · `BASELINE(0)` — 액션 열거지 이름표가 아니다
    if re.fullmatch(r"[a-z_]+\(\d+\)", low):
        return True
    # 영문 **산문**은 이름표가 아니다 — `M13(M06 now has full _EUI_TABLE data)` 는
    # 코드 주석 문장이지 M13 의 이름이 아니다. 영단어 3 개 이상 + 한글 없음이면 문장.
    return s.isascii() and len(s.split()) >= 3


#: 남의 낱말이 **더 긴 단어 안에** 우연히 들어간 경우. 한글은 낱말 경계가 없어
#  부분 문자열 매칭이 오탐을 만든다 — 실제로 "전열교환기" 의 "교환기" 를 '환기' 로
#  잡았다. 이런 걸 위반으로 세면 멀쩡한 설명을 고치게 된다.
FALSE_HOSTS = {
    "환기": ["교환기", "교환器", "열교환", "폐열회수", "열회수", "전열교환"],
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


#: **계열 안에서 서로를 가르는 낱말.** `통합`·`pmv`·`dr`·`셋백` 같은 공용 낱말만으로는
#  M11~M15·M19 가 서로 구별되지 않는다 — 사냥꾼 실증: **30 가지 상호 치환이 30/30 통과**.
#  그래서 계열 구성원마다 **자기만의 표식**을 요구한다.
EXCLUSIVE = {
    "M11": {"must_not": ["pmv", "프리미엄", "premium"]},
    "M12": {"must_not": ["pmv 0.7", "pmv0.7", "완전", "풀", "full", "프리미엄", "premium"]},
    "M13": {"must_not": ["pmv 0.5", "pmv0.5", "완전", "풀", "full", "프리미엄", "premium"]},
    "M14": {"must_not": ["프리미엄", "premium", "pmv0.5", "pmv 0.5", "pmv0.7", "pmv 0.7"]},
    "M15": {"must_not": ["완전", "full", "통합 ems", "통합ems", "combined_ems"]},
    "M19": {"must_not": ["긴급", "curtail", "통합 ems", "통합ems", "combined_ems"]},
    "M04": {"must_not": ["pmv 0.7", "pmv0.7"]},
    "M05": {"must_not": ["pmv 0.5", "pmv0.5"]},
    # ⚠ M00 정본이 "고정 설정온도 + 야간 Setback" 이라 **셋백은 M00 자신의 낱말**이다.
    #   그걸 배타로 넣었더니 정본 그대로 쓴 곳을 잡았다.
    "M00": {"must_not": ["dr", "긴급", "curtail"]},
    "M16": {"must_not": ["고정 설정온도", "baseline"]},
    "M10": {"must_not": ["긴급", "curtail", "통합", "셋백"]},
    "M20": {"must_not": ["통합 최적화", "통합최적화"]},
    "M07": {"must_not": ["폐열회수", "전열교환", "열회수", "erv"]},
    "M02": {"must_not": ["pmv", "보상"]},
}


#: `M11+M05` 처럼 **구성 레그를 코드로 적은 참조**. 배타 판정 전에 지운다 —
#  안 그러면 정본 그대로인 `M13(통합+PMV0.7 (M11+M05))` 이 "'05' 는 M13 의 표식이
#  아니다" 로 걸린다(실측). 규칙이 정본을 위반이라 부르면 그 규칙이 틀린 것이다.
_CODE_REF = re.compile(CODE, re.I)


#: 부정 표기 — `M02(외기냉방 (≠ PMV))` 는 "PMV 가 **아니다**" 라는 뜻이다.
#  이걸 "남의 표식을 달았다" 로 읽으면 정확한 구분 설명을 위반이라 부른다.
_NEGATION = re.compile(r"[≠≒!]=?|아님|아니|not\s|except|제외|vs\.?\s")


def check_exclusive(code: str, label: str) -> str | None:
    """계열 안에서 **남의 표식**을 달고 있는가."""
    if _NEGATION.search(label):
        return None
    # ⚠ 여기에 `_skip` 이 없어서 산문형 경로가 **영문 주석 문장까지** 판정했다
    #   (`M13(M06 now has full _EUI_TABLE data)`). 배타 규칙은 이름표에만 건다.
    if _skip(label):
        return None
    low = _CODE_REF.sub(" ", label.strip().lower())
    for bad in EXCLUSIVE.get(code, {}).get("must_not", []):
        if bad in low:
            return f"'{bad}' 는 {code} 의 표식이 아니다 — 같은 계열의 다른 전략이다"
    return None


def check_declared(code: str, label: str, st: dict) -> str | None:
    """선언형은 **정본 낱말이 하나라도 있어야** 한다(짧은 이름표일 때만)."""
    if _skip(label):
        return None
    # ⚠ **긴 설명문은 이름표가 아니다.** 남의 낱말이 섞여도 자연스럽다 —
    #   `M02("바깥 공기가 시원할 때 … 환기 팬을 돌리는 데 드는 전기가 …")` 는 M02 의
    #   정확한 설명이고, `M04("쾌적기준(PMV 0.5) 안에서 … 완화")` 도 맞는 설명이다.
    #   여기에 이름표 규칙을 들이대면 **멀쩡한 문장을 고치게 된다**.
    if len(label.strip()) > DESCRIPTION_LEN * 2:
        return None
    fk = check_foreign(code, label)
    if fk:
        return fk
    if len(label.strip()) > DESCRIPTION_LEN:
        # ⚠ 설명문에는 배타 규칙을 적용하지 않는다. `M11("스케줄 최적화+외기냉방+칠러
        #   대수제어 3종")` 은 **정확한 설명**인데 '최적화' 로 잡혔고, `M02("…환기 팬을
        #   돌리는 데 드는 전기가…")` 도 맞는 설명인데 '환기' 로 잡혔다. 설명은 자유롭다.
        return None
    ex = check_exclusive(code, label)
    if ex:
        return ex
    low = label.strip().lower()
    if any(k in low for k in SEMANTIC_KEYS.get(code, [])):
        return None
    e = st.get(code) or {}
    for nm in (e.get("name_en", ""), e.get("name_kr", "")):
        if nm and nm.lower() in low:
            return None
    return (f"정본은 '{e.get('name_kr', '?')}'({e.get('name_en', '?')}) 인데 "
            f"어느 낱말도 안 맞는다")


def _rel(p: Path, repo: Path) -> str:
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def scan(repo: Path, st: dict) -> list[tuple[str, int, str, str, str]]:
    out: list[tuple[str, int, str, str, str]] = []
    for p in iter_files(repo):
        out += scan_file(p, repo, st)
    return out


def scan_file(p: Path, repo: Path, st: dict) -> list[tuple[str, int, str, str, str]]:
    """파일 하나만 훑는다 — `--files`(pre-commit) 와 `scan()` 이 **같은 규칙**을 쓰도록."""
    out: list[tuple[str, int, str, str, str]] = []
    if True:
        try:
            # ⚠ 예전엔 8MB 넘는 `.jsonl` 을 **통째로 건너뛰었다** — 98 개가 사각지대였다.
            #   "안 본 것을 말한다" 고 적어 두고도 **안 본 건 그대로**였다.
            #   → 건너뛰지 않는다. 큰 파일은 **줄 단위로 흘려 읽어** M-code 가 있는 줄만
            #     모은다(줄 번호는 원본 기준으로 보존). 메모리는 한 줄씩만 든다.
            if p.suffix.lower() == ".jsonl" and p.stat().st_size > JSONL_MAX_BYTES:
                # ⚠ 전량 스트리밍은 **실행 불가능할 만큼 느렸다**(수십 GB, 저장소 하나에
                #   10 분+). **가드가 느리면 아무도 안 돌리고, 안 돌리는 가드는 없는 것이다**
                #   — 이번 세션에서 pre-commit 이 10 분을 넘겨 커밋을 막은 것과 같은 교훈.
                #   → **앞부분 표본**만 본다. 학습 코퍼스는 같은 생성기가 찍어낸 동질 행이라
                #     표본이 오염을 잡는다. 진짜 방어선은 **생성기 가드**다
                #     (`lab/scripts/verify_strategy_nl_ssot.py`). 여기선 그물만 친다.
                keep: list[str] = []
                with p.open(encoding="utf-8", errors="replace") as fh:
                    for _i, _l in enumerate(fh, 1):
                        if _i > JSONL_SAMPLE_LINES:
                            break
                        keep.append(_l.rstrip("\n") if re.search(CODE, _l) else "")
                text = "\n".join(keep)
            else:
                text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return out
        # ⚠ 빠른 걸러내기. 부분 문자열("M0")로 쓰면 SSOT pre-commit 이 이를
        #   "구 전략 코드 M0~M8 단독" 으로 잡는다(정당한 차단이다) → 정규식으로.
        if not re.search(CODE, text):
            return out
        for i, line in enumerate(text.splitlines(), 1):
            if HISTORICAL.search(line):
                continue
            # ⚠ **한 줄에 서로 다른 코드가 셋 이상이면 이름 짓는 자리가 아니다.**
            #   드리프트 진단 문서·감사표·핸드오프는 한 줄에 여러 코드를 늘어놓는다
            #   (`SSOT enum(#StrategyCode M00~M15) … M07(Lighting) … M11(조명/야간환기)`).
            #   거기서 짝을 뽑으면 **기록을 위반이라 부른다**. 이름은 한 번에 하나만 짓는다.
            if len(set(ENUMERATION.findall(line))) >= 3:
                continue
            seen = set()
            # 선언형 3 형태를 **같은 규칙으로** 본다. 예전엔 `DECLARED` 하나만 봐서
            # `"M09": [ … ]`(배열값)·`| M07 | NightCycle |`(표) 가 통째로 빠졌다.
            for rx in (DECLARED, ARRAY_DECLARED, TABLE):
                for m in rx.finditer(line):
                    code, label = m.group(1), m.group(2)
                    if (code, label) in seen:
                        continue
                    seen.add((code, label))
                    # 표는 **코드 옆 셀이 이름이라는 보장이 없다.** edge-agent 의
                    # 페르소나 표는 `| … | M20 | 저탄소·PV 잉여 충전 |` 처럼 DR 열
                    # 다음이 설명 열이다 — 그걸 이름표로 읽으면 멀쩡한 표를 고치게 된다.
                    # 그래서 표에는 산문과 같은 규칙(남의 낱말)만 건다.
                    # `| M07 | NightCycle |` 은 그것으로 충분히 잡힌다.
                    if rx is TABLE:
                        if not is_name_slot(label):
                            continue
                        why = check_foreign(code, label) or check_exclusive(code, label)
                    else:
                        why = check_declared(code, label, st)
                    if why:
                        out.append((_rel(p, repo), i, code, label.strip(), why))
            for m in PROSE.finditer(line):
                code, label = m.group(1), m.group(2)
                if (code, label) in seen:
                    continue
                # ⚠ 긴 산문 서술에 남의 낱말이 섞이는 건 자연스럽다 —
                #   `M02(… 환기 팬을 돌리는 데 드는 전기가 …)` 는 정확한 설명이다.
                #   이름표가 아니라 문장이므로 판정 대상이 아니다.
                if len(label.strip()) > DESCRIPTION_LEN * 2:
                    continue
                # ⚠ 예전엔 산문형에 **남의 낱말 검사만** 돌렸다. 그래서 남의 어휘가
                #   섞이지 않은 **그냥 틀린 이름**(`strategy=M07(냉방설정온도조정)`)이
                #   조용히 통과했다 — 2026-08-15 원 4 건 중 2 건이 이 구멍에 남아 있었다.
                #
                # ⚠ 그런데 여기에 **"정본 낱말이 없으면 위반"** 규칙까지 얹었더니
                #   **10,798 건**이 나왔다(실측). `M20(DR)`·`M09(SCHEDULE(20))`·
                #   `M15(운영 스케줄 최적화)` 같은 **부연**이 전부 걸렸다.
                #   산문 괄호는 이름을 **못박는 자리가 아니다** — 그러니 산문에는
                #   계획서 §5.3 그대로 **남의 낱말 규칙만** 적용한다.
                #   `strategy=M07(냉방설정온도조정)` 은 '설정온도'(=M04/M05 의 낱말)로
                #   잡힌다 — 그래서 FOREIGN 을 보강했지, 규칙을 넓힌 게 아니다.
                if not is_name_slot(label):
                    continue
                why = check_foreign(code, label) or check_exclusive(code, label)
                if why:
                    out.append((_rel(p, repo), i, code, label.strip(), why))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M-code 의미 교차 저장소 게이트")
    ap.add_argument("--repo", help="한 저장소만 검사(경로)")
    ap.add_argument("--strict", action="store_true", help="위반 시 exit 1")
    ap.add_argument("--limit", type=int, default=20, help="저장소당 표시 건수")
    # ⚠ **pre-commit 은 저장소를 통째로 훑으면 안 된다.** `.jsonl` 을 보게 한 뒤
    #   `8.simulation` 전량 스캔이 10 분을 넘겨 커밋을 막았다 — 가드가 느리면
    #   사람이 `--no-verify` 로 우회하고, 그러면 가드가 없는 것과 같다.
    ap.add_argument("--files", nargs="*", help="이 파일들만 검사(훅용). 저장소 스캔 생략")
    a = ap.parse_args(argv)

    st = canon()
    print("=" * 74)
    print(f"M-code 의미 게이트 — 정본 {len(st)}종 ({CANON_PATH.name})")
    print("  ⚠ ems_simulation/config/ems_strategies.yaml 은 폐기 세대(m0~m8). 정본 아님.")
    print("=" * 74)

    if a.files:
        base = Path(a.repo) if a.repo else Path.cwd()
        hits = []
        for f in a.files:
            fp = Path(f)
            if not fp.is_absolute():
                fp = base / f
            if not fp.is_file() or fp.suffix.lower() not in SCAN_EXT:
                continue
            if fp.resolve() == HERE or fp.stem.lower().startswith("scratch_"):
                continue
            if SKIP_PARTS & {x.lower() for x in fp.parts}:
                continue
            hits += scan_file(fp, base, st)
        # ⚠ 훅과 전체 스캔이 **다른 규칙**을 쓰면 안 된다. 여기에 논문 보류 규칙을
        #   안 걸어서, 전체 스캔은 0 건인데 커밋만 막히는 일이 실제로 났다.
        # ⚠ `--repo .` 이면 `Path('.').name` 이 **빈 문자열**이라 vintage 면제가 통째로
        #   안 걸렸다(훅이 자기 문서를 위반이라 막았다). 경로를 **해석해서** 이름을 낸다.
        rname = base.resolve().name
        def _vin(h):
            return is_vintage_pair(f"{rname}/{h[0]}", h[2], h[3])
        paper_hits = [h for h in hits
                      if not is_data_corpus(h[0]) and (is_paper_conflict(h[0]) or _vin(h))]
        code_hits = [h for h in hits if not is_data_corpus(h[0])
                     and not is_paper_conflict(h[0]) and not _vin(h)]
        for rel, ln, c, lab, why in code_hits:
            print(f"  ⛔ {rel}:{ln}  {c}({lab})  ← {why}")
        if paper_hits:
            print(f"  ℹ️  reverse vintage 표기 {len(paper_hits)}건 — 위반 아님(실측 확정).")
            print(f"     근거 = {PAPER_CONFLICT_DOC}")
        n_corpus = len(hits) - len(code_hits) - len(paper_hits)
        if n_corpus:
            print(f"  ℹ️  학습 코퍼스 {n_corpus}건 — 재증류 대상(생성기에서 막는다)")
        if code_hits:
            print(f"⛔ 오매핑 {len(code_hits)}건")
            return 1
        print(f"✅ 파일 {len(a.files)}개 — 오매핑 없음")
        return 0

    repos = [Path(a.repo)] if a.repo else [WORKSPACE / r for r in REPOS]
    total = scanned = corpus_total = paper_total = 0
    corpus_files: set[str] = set()
    for repo in repos:
        if not repo.is_dir():
            print(f"  ⏭ 없음: {repo}")
            continue
        scanned += 1
        label = repo.name or str(repo)
        all_hits = scan(repo, st)
        corpus = [h for h in all_hits if is_data_corpus(h[0])]
        def _vintage(h):
            return is_vintage_pair(f"{label}/{h[0]}", h[2], h[3])
        paper = [h for h in all_hits
                 if not is_data_corpus(h[0]) and (is_paper_conflict(h[0]) or _vintage(h))]
        paper_total += len(paper)
        hits = [h for h in all_hits if not is_data_corpus(h[0])
                and not is_paper_conflict(h[0]) and not _vintage(h)]
        corpus_total += len(corpus)
        if corpus:
            corpus_files.update(h[0] for h in corpus)
        if not hits:
            print(f"  ✅ {label}" + (f"   (학습 코퍼스 {len(corpus)}건 — 재증류 대상)"
                                     if corpus else ""))
            continue
        print(f"  ⛔ {label} — {len(hits)}건"
              + (f"   (+ 학습 코퍼스 {len(corpus)}건)" if corpus else ""))
        lim = len(hits) if a.limit == 0 else a.limit   # 0 = 전부 (감추지 않는다)
        for rel, ln, code, lab, why in hits[:lim]:
            print(f"       {rel}:{ln}  {code}({lab})  ← {why}")
        if len(hits) > lim:
            print(f"       … 외 {len(hits) - a.limit}건")
        total += len(hits)

    print("-" * 74)
    if paper_total:
        print(f"ℹ️  reverse 계열 vintage 표기 {paper_total}건 — **위반이 아니다.**")
        print("   7번째 비트 = E1(NightCycle) 로 실측 확정됐다. 그 저장소의 M07=NightCycle ·")
        print("   M06=DCV 는 2026-05-13 이전 매핑의 **정확한 이름**이다(정본 잣대는 범주 오류).")
        print(f"   근거·이름 통일 순서 = {PAPER_CONFLICT_DOC}")
    if corpus_total:
        print(f"ℹ️  학습 코퍼스 {corpus_total}건 / 파일 {len(corpus_files)}개 — **재증류 대상**이다.")
        print("   과거 생성물을 손편집하면 수정이 아니라 데이터 변조다. 고칠 곳은 생성기다.")
        print("   라이브 학습 입력의 정합은 agentleague/scripts/validate_corpus_mcode_ssot.py 가 잰다.")
    # ⚠ **안 본 것을 말한다.** 상한에 걸려 건너뛴 파일을 조용히 넘기면 그게 다음
    #   사각지대가 된다 — 이번 라운드가 통째로 그 교훈이었다.
    if SKIPPED_TOO_BIG:
        print(f"ℹ️  크기 상한({JSONL_MAX_BYTES // 1024 // 1024}MB) 초과 .jsonl "
              f"{len(SKIPPED_TOO_BIG)}개 — **앞 {JSONL_SAMPLE_LINES:,}행 표본으로 봤다**"
              f"(예전엔 통째로 건너뛰어 사각지대였다):")
        for s in SKIPPED_TOO_BIG[:5]:
            print(f"     {s}")
        if len(SKIPPED_TOO_BIG) > 5:
            print(f"     … 외 {len(SKIPPED_TOO_BIG) - 5}개")
        print("   → 학습 코퍼스는 라벨 게이트가 아니라 **생성기**에서 막는다"
              " (lab/scripts/verify_strategy_nl_ssot.py).")
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
