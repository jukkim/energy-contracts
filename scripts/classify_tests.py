"""테스트 자동 분류 도구 (Phase G).

SSOT: schemas/test_classification.json — Tier × Group × Stage 3축
워크스페이스의 모든 `tests/**/test_*.py` 를 스캔하여:
  - Tier 추정: 파일 경로(tests/unit→T2, tests/integration→T3, ...) + import 분석
  - Group 추정: 프로젝트별 project_default_groups + 키워드 분석
  - Stage 추정: Tier 기반 (T0/T1→S1, T2→S2, T3→S3, T4→S4, T5→S5)

사용법:
  python classify_tests.py --dry-run         # 분류 결과만 출력
  python classify_tests.py --report          # 카운트 통계만
  python classify_tests.py --apply <file>    # 특정 파일에 marker 안내 출력
  python classify_tests.py --apply-all       # 전 워크스페이스에 파일 헤더 marker 자동 부여

이 도구는 70~80% 자동 분류. cross-cutting (G6 Auth-RBAC)은 수동 보강 권장.
--apply-all 은 파일별 `pytestmark = [pytest.mark.tier(...), ...]` 모듈 레벨 marker
방식으로 부여 — 함수마다 데코레이터를 다는 것보다 안전하고 회귀가 없다.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]
SCHEMA = json.loads(
    (CONTRACTS_ROOT / "energy_contracts" / "schemas" / "test_classification.json").read_text(encoding="utf-8")
)
DEFAULT_GROUPS: dict[str, list[str]] = SCHEMA["default"]["project_default_groups"]

# ── Tier 추정 규칙 ──────────────────────────────────────────────────────────

TIER_FOLDER_HINT = {
    "unit":        "T2",
    "integration": "T3",
    "e2e":         "T4",
    "ui":          "T5",
    "contract":    "T1",
    "fixture":     "T0",
}

TIER_IMPORT_HINT = [
    (re.compile(r"\bfrom\s+playwright|import\s+playwright"), "T5"),
    (re.compile(r"\bfrom\s+selenium"),                       "T5"),
    (re.compile(r"\bjsonschema\b"),                          "T1"),
    (re.compile(r"\bsqlalchemy.*create_engine|psycopg2"),    "T3"),
    (re.compile(r"\bredis\.Redis|paho\.mqtt"),               "T3"),
    (re.compile(r"\bhttpx\.AsyncClient|TestClient.*localhost:\d+"), "T4"),
]

# ── Mock 패턴 검출 (M-7a) ───────────────────────────────────────────────────
# import hint 만으로는 mock 기반 unit 과 실 통합을 구분 못함
# (예: paho.mqtt 를 import 하지만 MagicMock 으로 대체하는 경우).
# folder hint (tests/integration/, tests/e2e/) 는 의도적 분리라 신뢰하되,
# import hint 단독은 mock 패턴 검출 시 T2 로 강등한다.
_MOCK_IMPORT_PATTERNS = (
    re.compile(r"from\s+unittest\.mock\s+import"),
    re.compile(r"\bimport\s+unittest\.mock\b"),
    re.compile(r"\b(MagicMock|AsyncMock|PropertyMock)\s*\("),
)
_MOCK_INTENT_HINTS = (
    "mock으로", "mock 으로", "magicmock", "asyncmock",
    "브로커 없이", "broker 없이", "without broker",
    "전부 mock", "모두 mock", "db 호출은",
)


def _is_mock_based(text: str) -> bool:
    """파일이 mock 위주로 동작하는지 휴리스틱 검출.

    True 인 케이스:
      1) unittest.mock import + MagicMock/AsyncMock/PropertyMock 실호출
      2) 모듈 docstring/주석 헤더에 mock 의도 키워드 포함
    """
    head = text[:4000]
    for rx in _MOCK_IMPORT_PATTERNS:
        if rx.search(head):
            return True
    head_lower = head.lower()
    return any(hint in head_lower for hint in _MOCK_INTENT_HINTS)


def estimate_tier(fp: Path, text: str) -> str:
    """파일 경로 + import 로 tier 추정. default=T2.

    folder hint 는 항상 신뢰 (의도된 분리). import hint 는 mock 패턴 동시
    검출 시 T3/T4 → T2 로 강등하여 false positive 차단.
    """
    parts_lower = [p.lower() for p in fp.parts]
    for hint, tier in TIER_FOLDER_HINT.items():
        if hint in parts_lower:
            return tier
    head = text[:3000]
    for rx, tier in TIER_IMPORT_HINT:
        if rx.search(head):
            if tier in ("T3", "T4") and _is_mock_based(text):
                return "T2"
            return tier
    return "T2"


# G6 (Auth-RBAC) cross-cutting 부여 키워드.
# 'scope' 단어는 carbon Scope1/2/3, lighting/zoom scope 등 광범위 오탐 — 제외하고
# 'auth_scope', 'oauth_scope', 'rbac_scope' 같은 합성어만 매치.
# SSOT: 향후 test_classification.json#group_keyword_hints.G6 로 이동 예정.
#
# 사냥꾼 라운드 LOW (2026-06-08): 기존엔 'token'/'session'/'cookie' 를 파일명 substring 으로
#   매치해 test_token_bucket.py(rate limiter)·test_engineering_session.py(commissioning)
#   같은 auth 무관 테스트가 G6 오부여됐다. → 명확한 auth 토큰만 word-boundary 로 매치하고,
#   모호한 token/session/cookie 는 파일명 단독으로는 부여하지 않고 본문 import 시그널에 위임.
_AUTH_STRONG_NAME_RE = re.compile(
    r"(?:^|[_\-.])(?:auth|rbac|oauth|jwt|login|logout|csrf|api[_-]?key|permission)s?(?=$|[_\-.])"
)
_AUTH_RBAC_IMPORT_PAT = re.compile(
    r"(from\s+src\.auth|import\s+jwt|jwt\.(decode|encode)|HTTPBearer|"
    r"require_auth|check_permission|AUTH_JWT_POLICY|AUTH_SCOPES)"
)


def _is_auth_test(fp: Path, text: str | None = None) -> bool:
    """파일명/import 분석으로 G6 (Auth-RBAC) cross-cutting 판정.

    1) 파일명에 명확한 auth 토큰 포함 (auth/rbac/oauth/jwt/login/logout/csrf/api_key/permission)
       — word-boundary 매치 (substring 오탐 방지)
    2) 본문에 auth 관련 import/심볼 포함 (jwt.decode, HTTPBearer, require_auth, ...)
       — 모호한 session/token/cookie 류는 이 본문 시그널이 있을 때만 G6.
    """
    name = fp.name.lower()
    if _AUTH_STRONG_NAME_RE.search(name):
        return True
    if text is None:
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return False
    head = text[:4000]
    return bool(_AUTH_RBAC_IMPORT_PAT.search(head))


def estimate_groups(fp: Path, text: str | None = None) -> list[str]:
    """프로젝트 폴더로 group 추정. project_default_groups 전체를 반환.

    Returns: [primary, ...secondary] — primary는 첫 group marker로,
             secondary는 추가 group marker로 부여.

    G6 (Auth-RBAC) cross-cutting 부여 정책:
      - 파일명/본문 import 분석으로 auth 시그널 검출 시에만 부여.
      - project_default_groups 가 G6 를 포함하더라도 시그널 없으면 제거 —
        "모든 backend 테스트가 G6" 무차별 부여 방지 (H7 정정).
    """
    parts = [p for p in fp.parts]
    groups: list[str] = []
    for proj, default_groups in DEFAULT_GROUPS.items():
        if proj in parts and default_groups:
            groups = list(default_groups)
            break
    if not groups:
        groups = ["G2"]  # default Backend
    is_auth = _is_auth_test(fp, text)
    if is_auth and "G6" not in groups:
        groups.append("G6")
    elif not is_auth and "G6" in groups:
        groups.remove("G6")
    return groups


_TIER_STAGE_MAP = {"T0": "S1", "T1": "S1", "T2": "S2", "T3": "S3",
                   "T4": "S4", "T5": "S5"}


def estimate_stage(tier: str) -> str:
    # 새 tier (T6/T7) 추가 시 silent S3 폴백 대신 명시 매핑을 강제.
    if tier not in _TIER_STAGE_MAP:
        raise KeyError(
            f"unknown tier={tier!r}; _TIER_STAGE_MAP 갱신 필요 "
            f"(현재 매핑: {sorted(_TIER_STAGE_MAP)})"
        )
    return _TIER_STAGE_MAP[tier]


# ── 스캔 ─────────────────────────────────────────────────────────────────────

def scan_tests() -> list[tuple[Path, str, list[str], str]]:
    """전체 워크스페이스 테스트 파일 + 추정 (Tier, Groups, Stage).

    `{proj}/tests/` 직속 + `{proj}/backend/tests/` (eduarena, agentleague 등) 둘 다 스캔.
    Groups는 list — primary + cross-cutting (G6) 동시 부여 지원.
    """
    out: list[tuple[Path, str, list[str], str]] = []
    projects_dir = WORKSPACE_ROOT / "projects"
    if not projects_dir.exists():
        return out
    test_root_candidates = ("tests", "backend/tests")
    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir():
            continue
        for sub in test_root_candidates:
            tests_dir = proj_dir.joinpath(*sub.split("/"))
            if not tests_dir.is_dir():
                continue
            for fp in tests_dir.rglob("test_*.py"):
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                tier = estimate_tier(fp, text)
                groups = estimate_groups(fp, text)
                stage = estimate_stage(tier)
                out.append((fp, tier, groups, stage))
    return out


def report(entries: list[tuple[Path, str, list[str], str]]) -> None:
    from collections import Counter
    tier_c = Counter(e[1] for e in entries)
    # 그룹 카운트: primary만 + 전체(중복 포함)
    group_primary_c = Counter(e[2][0] for e in entries)
    group_all_c = Counter(g for e in entries for g in e[2])
    stage_c = Counter(e[3] for e in entries)
    print(f"총 {len(entries)}개 테스트 파일")
    print(f"  Tier:           {dict(tier_c)}")
    print(f"  Group (primary):{dict(group_primary_c)}")
    print(f"  Group (all):    {dict(group_all_c)}")
    print(f"  Stage:          {dict(stage_c)}")


def dry_run(entries: list[tuple[Path, str, list[str], str]]) -> None:
    for fp, tier, groups, stage in entries:
        rel = fp.relative_to(WORKSPACE_ROOT)
        print(f"  {tier} {'+'.join(groups)} {stage}  {rel}")


# ── --apply-all 모듈 레벨 marker 자동 삽입 ──────────────────────────────────

_MARKER_BLOCK_HEAD = "# ─ Phase G SSOT markers (auto-applied by classify_tests.py) ─"
_MARKER_BLOCK_TAIL = "# ─ End Phase G markers ─"


def _build_marker_block(tier: str, groups: list[str] | str, stage: str) -> str:
    if isinstance(groups, str):
        groups = [groups]
    group_lines = "".join(
        f"    _ssot_pytest.mark.group({g!r}),\n" for g in groups
    )
    return (
        f"{_MARKER_BLOCK_HEAD}\n"
        f"import pytest as _ssot_pytest\n"
        f"pytestmark = [\n"
        f"    _ssot_pytest.mark.tier({tier!r}),\n"
        f"{group_lines}"
        f"    _ssot_pytest.mark.stage({stage!r}),\n"
        f"]\n"
        f"{_MARKER_BLOCK_TAIL}\n"
    )


_LEGACY_MARKER_HEAD = re.compile(
    r"#\s*─+\s*Phase G SSOT markers"
    r"(?! \(auto-applied by classify_tests\.py\))"
    r"[^\n]*\n"
)
_LEGACY_MARKER_TAIL = re.compile(r"#\s*─+\s*End Phase G markers\s*─*\s*\n?")


def _strip_legacy_marker_blocks(text: str) -> str:
    """변형 헤더로 들어간 중복 marker 블록만 제거.

    canonical 헤더(`(auto-applied by classify_tests.py)` 포함)는 보존하여
    `_apply_marker_to_file` 가 in-place 교체로 주변 공백을 유지하도록 한다
    (apply-all 시 무관 파일에 whitespace drift 방지).
    """
    while True:
        m_head = _LEGACY_MARKER_HEAD.search(text)
        if not m_head:
            return text
        m_tail = _LEGACY_MARKER_TAIL.search(text, m_head.end())
        if not m_tail:
            return text
        # 블록 사이 영역도 함께 제거 (pytestmark = [...] + import pytest as _ssot_pytest)
        text = text[: m_head.start()] + text[m_tail.end():]


def _strip_headerless_pytestmark(text: str) -> str:
    """canonical sentinel 블록 외부의 모듈 레벨 pytestmark = [...] 제거.

    `_strip_legacy_marker_blocks` 는 헤더 sentinel 변형만 다룬다.
    sentinel 자체가 없는 raw `pytestmark = [...]` 는 감지하지 못해 중복 발생.
    AST 로 모듈 레벨 Assign(target=Name('pytestmark')) 를 찾아 canonical
    블록 내부가 아닌 것만 제거. 직전 라인이 `import pytest as _ssot_pytest`
    면 함께 제거 (dangling import 방지).

    TD-6 (2026-05-18): test_building_permits_api.py 1건 실증.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    lines = text.splitlines(keepends=True)
    to_remove: list[tuple[int, int]] = []  # (start_idx, end_idx) 0-indexed, end exclusive
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "pytestmark"):
            continue
        start = node.lineno - 1  # 0-indexed
        end = (node.end_lineno or node.lineno)  # 1-indexed inclusive → exclusive
        # 위쪽 6줄 안에 canonical header 가 있으면 보존 (sentinel block 내부 pytestmark).
        # 4 → 6 으로 여유 확보: docstring/주석/빈줄이 끼어도 false negative 차단.
        window_start = max(0, start - 6)
        window = "".join(lines[window_start:start])
        if _MARKER_BLOCK_HEAD in window:
            continue
        # 직전 라인이 `import pytest as _ssot_pytest` 이면 함께 제거
        adj_start = start
        if start > 0 and lines[start - 1].strip() == "import pytest as _ssot_pytest":
            # 그 위가 canonical header 가 아닐 때만 제거
            window2 = "".join(lines[max(0, start - 7):start - 1])
            if _MARKER_BLOCK_HEAD not in window2:
                adj_start = start - 1
        to_remove.append((adj_start, end))
    # 뒤에서부터 제거 (인덱스 보존)
    for s, e in reversed(to_remove):
        del lines[s:e]
    return "".join(lines)


def _apply_marker_to_file(fp: Path, tier: str, groups: list[str] | str, stage: str) -> str:
    """파일에 모듈 레벨 marker 블록 삽입. 이미 있으면 갱신.

    삽입 위치: future import / docstring 다음, 첫 코드 라인 이전.
    변형 헤더로 들어간 중복 블록도 한 번에 정리 (idempotent 강화).
    """
    text = fp.read_text(encoding="utf-8")
    text = _strip_legacy_marker_blocks(text)
    text = _strip_headerless_pytestmark(text)
    # 이미 marker 블록이 있으면 통째로 교체 (idempotent) — 이 시점엔 정규형 블록 0개 또는 1개
    if _MARKER_BLOCK_HEAD in text and _MARKER_BLOCK_TAIL in text:
        before, _rest = text.split(_MARKER_BLOCK_HEAD, 1)
        _block, after = _rest.split(_MARKER_BLOCK_TAIL, 1)
        # tail 줄바꿈 정리
        after = after.lstrip("\n")
        new_text = before + _build_marker_block(tier, groups, stage) + after
    else:
        # 삽입 지점 찾기: 모듈 docstring + future imports 다음
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return "skip-syntax"
        # 첫 non-docstring + non-future-import 노드의 라인 번호
        insert_line = 0
        for node in tree.body:
            # docstring
            if (isinstance(node, ast.Expr) and
                isinstance(node.value, ast.Constant) and
                isinstance(node.value.value, str)):
                insert_line = node.end_lineno or node.lineno
                continue
            # __future__ import
            if (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
                insert_line = node.end_lineno or node.lineno
                continue
            break
        lines = text.splitlines(keepends=True)
        block = _build_marker_block(tier, groups, stage)
        # insert_line 다음 줄에 빈 줄 + 블록 삽입
        prefix = "".join(lines[:insert_line])
        suffix = "".join(lines[insert_line:])
        sep_before = "" if prefix.endswith("\n\n") else ("\n" if prefix.endswith("\n") else "\n\n")
        sep_after = "\n" if suffix and not suffix.startswith("\n") else ""
        new_text = prefix + sep_before + block + sep_after + suffix

    if new_text == text:
        return "same"
    fp.write_text(new_text, encoding="utf-8")
    return "wrote"


def apply_all(entries: list[tuple[Path, str, list[str], str]]) -> int:
    """전 워크스페이스 marker 자동 부여. 회귀 안전 모듈 레벨 방식."""
    from collections import Counter
    stats = Counter()
    for fp, tier, groups, stage in entries:
        status = _apply_marker_to_file(fp, tier, groups, stage)
        stats[status] += 1
    print(f"[classify_tests] apply-all 완료: {dict(stats)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",   action="store_true", help="분류 결과 출력 (수정 안함)")
    ap.add_argument("--report",    action="store_true", help="카운트 통계만")
    ap.add_argument("--apply",     help="해당 파일에 marker 안내 출력 (단일 파일)")
    ap.add_argument("--apply-all", action="store_true",
                    help="전 워크스페이스 marker 자동 부여 (모듈 레벨 pytestmark)")
    args = ap.parse_args()

    entries = scan_tests()
    if args.report:
        report(entries)
        return 0
    if args.apply_all:
        return apply_all(entries)
    if args.apply:
        target = Path(args.apply).resolve()
        for fp, tier, groups, stage in entries:
            if fp == target:
                primary = groups[0]
                print(f"수동 적용 예시 ({tier}/{'+'.join(groups)}/{stage}):")
                print(f"@pytest.mark.tier('{tier}')")
                for g in groups:
                    print(f"@pytest.mark.group('{g}')")
                print(f"@pytest.mark.stage('{stage}')")
                print(f"def test_xxx(...): ...")
                return 0
        print(f"[classify_tests] {args.apply} 미발견")
        return 1
    # default: dry-run + report
    dry_run(entries)
    print()
    report(entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
