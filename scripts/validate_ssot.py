"""SSOT 위반 검사기 — pre-commit / CI 용도.

검사 항목:
  1. 하드코딩된 구 전략 코드 (M0, M1, ..., M8 단독) 탐지
  2. 포트 할당 충돌 (port_allocation.json 기준)
  3. JSON Schema 일관성 (common.json $defs 와 다른 스키마 정합)
  4. _generated_constants.* SOURCE_HASH drift (Phase H 추가)
  5. port_range 슬롯과 단일 port 항목의 잠복 충돌 (Phase H 추가)
  6. SSOT _usage / _consumers 헤더 (Phase M-3 추가)
     - 모든 schema 가 _usage ∈ {codegen, runtime-validate, reference-only, hybrid} 보유
     - _usage=codegen 인데 gen_constants.py load_schemas() 미참조 시 위반

사용법:
  python validate_ssot.py [--check strategy|ports|schemas|generated|all] [paths...]
  python validate_ssot.py --check all  # 기본
  python validate_ssot.py --check strategy ../edge-agent/src
  python validate_ssot.py --pre-commit  # 변경된 파일만 검사

종료 코드:
  0 — 통과 / 1 — 위반 발견 / 2 — 검사 자체 오류
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = CONTRACTS_ROOT / "energy_contracts" / "schemas"
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]  # myjob/

# ── 1. 전략 코드 ─────────────────────────────────────────────────────────────

# 구 코드(M0~M8) 패턴 — string literal 안에서만 매칭하여 false positive 최소화
# "M5", 'M5' 형태 (식별자 P3-M2 등은 제외)
LEGACY_STRATEGY_RE = re.compile(r"""['"](M[0-8])['"]""")

# 파일 레벨 면제 마커
FILE_EXEMPT_MARKERS = (
    "SSOT_ALLOW_LEGACY_STRATEGY",  # 의도된 negative test 파일
    "AUTO-GENERATED",              # gen_constants.py 산출물
)

# 예외 허용 경로 — 마이그레이션 주석/문서/CHANGELOG 등
STRATEGY_EXEMPT_PATTERNS = [
    "AUDIT-",       # 감사 보고서 (마이그레이션 기록)
    "CHANGELOG",
    "MIGRATION",
    "REVIEW",
    "/reviews/",
    "validate_ssot.py",
    "SSOT_GOVERNANCE",
    "ems_strategies.json",  # SSOT 자체
    "/scratch/",            # 임시 작업 공간
]

# 검사 대상 확장자
STRATEGY_SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".html", ".yaml", ".yml"}


def scan_legacy_strategies(paths: list[Path]) -> list[tuple[Path, int, str]]:
    violations = []
    for root in paths:
        if root.is_file():
            files = [root]
        else:
            files = [p for p in root.rglob("*") if p.is_file()
                     and p.suffix in STRATEGY_SCAN_EXTS]
        for fp in files:
            s = str(fp).replace("\\", "/")
            if any(pat in s for pat in STRATEGY_EXEMPT_PATTERNS):
                continue
            # 라이브러리/빌드 산출물 스킵
            if any(part in fp.parts for part in
                   ("node_modules", "dist", ".git", ".venv", "venv", "env",
                    "__pycache__", "build", "site-packages", ".next", "out")):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # 파일 레벨 면제 마커
            if any(marker in text for marker in FILE_EXEMPT_MARKERS):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                # 주석 라인 건너뜀 (마이그레이션 메모 허용)
                stripped = line.lstrip()
                if stripped.startswith(("#", "//", "*", "<!--")):
                    continue
                # 라인 후미 주석 안의 노트 (어디든 invalid/legacy 키워드) 면제
                if re.search(r"#.*\b(old|legacy|negative|rejected|invalid)\b",
                             line, re.I):
                    continue
                if re.search(r"//.*\b(old|legacy|negative|rejected|invalid)\b",
                             line, re.I):
                    continue
                if LEGACY_STRATEGY_RE.search(line):
                    violations.append((fp, lineno, line.strip()[:120]))
    return violations


# ── 2. 포트 충돌 ─────────────────────────────────────────────────────────────

def load_port_allocation() -> dict:
    fp = SCHEMAS_DIR / "port_allocation.json"
    if not fp.exists():
        return {}
    return json.loads(fp.read_text(encoding="utf-8"))


def check_port_conflicts() -> list[str]:
    """동일 포트에 둘 이상의 deployed 서비스 매핑 시 위반.

    Phase H: port_range 슬롯이 단일 port 항목과 겹치는지 잠복 검사.
    """
    data = load_port_allocation()
    if not data:
        return ["port_allocation.json 미존재"]
    seen: dict[int, list[str]] = defaultdict(list)
    all_seen: dict[int, list[tuple[str, str]]] = defaultdict(list)  # 사냥꾼 LOW: 전 status
    ranges: list[tuple[int, int, str, str]] = []  # (lo, hi, name, status)
    for svc in data.get("services", []):
        port = svc.get("port")
        port_range = svc.get("port_range")
        if port_range:
            # "8011-8016" 형태
            try:
                lo_s, hi_s = port_range.split("-")
                ranges.append((int(lo_s), int(hi_s),
                               svc.get("name", "?"), svc.get("status", "?")))
            except ValueError:
                pass
            continue
        if port is None:
            continue
        # machine_override로 blocked인 항목은 충돌에서 제외
        if svc.get("machine_override", {}).get("A") == "blocked (Docker)":
            continue
        status = svc.get("status", "?")
        all_seen[port].append((svc.get("name", "?"), status))
        if status != "deployed":
            continue
        seen[port].append(svc.get("name", "?"))
    violations = []
    for port, names in seen.items():
        if len(names) > 1:
            violations.append(f"포트 {port} 중복: {', '.join(names)}")
    # port_range 잠복 충돌 (deployed 단일 port와 겹침)
    for lo, hi, rng_name, rng_status in ranges:
        for port, names in seen.items():
            if lo <= port <= hi:
                # multi-mode dormant 는 잠복 표시만 (warning, not failure)
                if rng_status == "multi-mode":
                    continue
                violations.append(
                    f"포트 {port} ({names[0]}) 가 range {lo}-{hi} ({rng_name}, {rng_status}) 와 충돌")
    # 사냥꾼 라운드 LOW (2026-06-08): 비-deployed(dev/scaffold/training-pending) 포함 잠복
    #   포트 중복은 실패(deployed-deployed)는 아니나 dev→deployed 승격 시 충돌 위험 → 경고만.
    warnings = []
    for port, entries in all_seen.items():
        if len(entries) > 1:
            deployed_n = sum(1 for _, s in entries if s == "deployed")
            if deployed_n <= 1:  # deployed-deployed 는 위에서 이미 violation 처리
                names = ", ".join(f"{n}({s})" for n, s in entries)
                warnings.append(f"포트 {port} 잠복 중복(비-deployed 포함): {names}")
    if warnings:
        print(f"[SSOT] 포트 잠복 충돌 경고 {len(warnings)}건 (비-deployed — 실패 아님):")
        for w in warnings:
            print(f"  - {w}")
    return violations


# ── 4. _generated_constants.* SOURCE_HASH drift (Phase H) ──────────────────

GENERATED_TARGETS: list[tuple[str, str]] = [
    ("python", "projects/edge-agent/src/_generated_constants.py"),
    ("python", "projects/gridbridge/src/_generated_constants.py"),
    ("python", "projects/building-energy-3d/src/shared/_generated_constants.py"),
    ("ts",     "projects/building-energy-3d/frontend/src/shared/_generated_constants.ts"),
    ("python", "projects/agentleague/backend/_generated_constants.py"),
    ("python", "projects/eduarena/backend/_generated_constants.py"),
]


def check_generated_drift() -> list[str]:
    """_generated_constants.* 파일의 SOURCE_HASH 헤더 vs 실 schemas hash 비교.

    수동 편집된 파일을 탐지한다. gen_constants.py와 동일 알고리즘.

    한계 (사냥꾼 라운드 M5, 2026-06-08): 본 검사는 16자 SOURCE_HASH **헤더만** 비교한다.
    schemas_hash 는 (schemas dict + gen_constants.py self bytes) 로만 계산되므로, 생성
    파일 **본문 상수값** 을 손으로 변조하면서 헤더를 유지하면 본 검사는 통과한다.
    본문 전체 정합은 `python gen_constants.py --check` (out.read_text() != 재생성 content
    full-compare) 가 담당하며, pre-commit hook 이 두 검사를 함께 실행한다. validate_ssot
    단독으로는 본문 변조를 보장하지 못하므로, CI/로컬 게이트는 gen --check 를 동반해야 한다.
    """
    violations: list[str] = []
    try:
        import importlib.util
        gen_path = CONTRACTS_ROOT / "scripts" / "gen_constants.py"
        spec = importlib.util.spec_from_file_location("gen_constants", gen_path)
        if spec is None or spec.loader is None:
            return ["gen_constants.py 로드 실패"]
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        schemas = gen.load_schemas()
        expected_hash = gen.schemas_hash(schemas)
    except Exception as e:
        return [f"schemas hash 계산 실패: {e}"]

    py_pat = re.compile(r'SOURCE_HASH\s*=\s*"([0-9a-f]{16})"')
    ts_pat = re.compile(r'export const SOURCE_HASH\s*=\s*"([0-9a-f]{16})"')
    skipped: list[str] = []
    for lang, rel in GENERATED_TARGETS:
        fp = WORKSPACE_ROOT / rel
        # 형제 repo 자체가 없거나 빈 디렉토리(repo marker 없음)면 CI 단일 repo
        # 체크아웃으로 간주 → 스킵. 각 형제 repo 자체 pre-commit hook + 자체 CI 가 검증.
        # 빈 디렉토리 우회 방지(M5): .git/pyproject.toml/package.json 중 하나가 있어야 진짜 repo.
        sibling_repo_root = WORKSPACE_ROOT / rel.split("/")[0] / rel.split("/")[1]
        if not sibling_repo_root.exists():
            skipped.append(rel)
            continue
        repo_markers = (".git", "pyproject.toml", "package.json", "Cargo.toml")
        if not any((sibling_repo_root / m).exists() for m in repo_markers):
            skipped.append(f"{rel} (빈 디렉토리 — repo marker 없음)")
            continue
        if not fp.exists():
            violations.append(f"{rel}  생성 파일 없음 — `gen_constants.py --all` 실행 필요")
            continue
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(f"{rel}  읽기 실패: {e}")
            continue
        m = (py_pat if lang == "python" else ts_pat).search(text)
        if not m:
            violations.append(f"{rel}  SOURCE_HASH 헤더 누락 — 수동 편집 의심")
            continue
        actual = m.group(1)
        if actual != expected_hash:
            violations.append(
                f"{rel}  SOURCE_HASH drift (file={actual} expected={expected_hash}) "
                f"— `gen_constants.py --all` 재실행 필요")
    if skipped:
        # 스킵 카운트는 print 로 알리고 (CI 로그 가시화), violations 에는 넣지 않음.
        print(f"[SSOT] 형제 repo {len(skipped)}건 스킵 (CI 단일 repo 환경 또는 빈 dir):")
        for s in skipped:
            print(f"  - {s}")
    return violations


# ── 3. JSON Schema 일관성 ───────────────────────────────────────────────────

STRATEGY_PATTERN_EXPECTED = r"^M(0[0-9]|1[0-9]|20)$"


def check_schema_strategy_patterns() -> list[str]:
    """JSON Schema 파일이 구 패턴 ^M[0-8]$ 사용 시 위반 — pattern 키만 검사."""
    violations = []
    # "pattern": "^M[0-8]..." 형태만 매칭 (description 안의 설명문은 제외)
    bad_pattern = re.compile(r'"pattern"\s*:\s*"\^M\[0-8\]')
    for fp in SCHEMAS_DIR.glob("*.json"):
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if bad_pattern.search(line):
                violations.append(
                    f"{fp.name}:{lineno}  구 strategy pattern 발견: {line.strip()[:100]}")
    return violations


# ── 6. SSOT _usage / _consumers 헤더 (Phase M-3) ────────────────────────────

VALID_USAGE_VALUES = {"codegen", "runtime-validate", "reference-only", "hybrid"}


def check_schema_usage_headers() -> list[str]:
    """49 schemas 가 모두 `_usage` + `_consumers` 헤더를 가지는지 검사.

    추가 검증:
      - _usage ∈ {codegen, runtime-validate, reference-only, hybrid}
      - _consumers 는 list[str]
      - _usage=codegen / hybrid 인 schema 는 gen_constants.py load_schemas() 본문에서
        파일명 문자열이 등장해야 한다 (codegen 미연결 검출)
    """
    violations: list[str] = []
    gen_src = ""
    gen_fp = CONTRACTS_ROOT / "scripts" / "gen_constants.py"
    if gen_fp.exists():
        gen_src = gen_fp.read_text(encoding="utf-8")

    for fp in sorted(SCHEMAS_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            violations.append(f"{fp.name}  JSON 파싱 실패: {e}")
            continue
        usage = data.get("_usage")
        consumers = data.get("_consumers")
        if usage is None:
            violations.append(f"{fp.name}  `_usage` 필드 누락 (M-3)")
            continue
        if usage not in VALID_USAGE_VALUES:
            violations.append(
                f"{fp.name}  `_usage`={usage!r} 유효값 아님 "
                f"(허용: {sorted(VALID_USAGE_VALUES)})")
            continue
        if not isinstance(consumers, list):
            violations.append(
                f"{fp.name}  `_consumers` 필드 누락 또는 list 아님 "
                f"(타입={type(consumers).__name__})")
            continue
        if any(not isinstance(c, str) for c in consumers):
            violations.append(f"{fp.name}  `_consumers` 항목은 str 이어야 함")
            continue
        # codegen / hybrid 는 gen_constants.py 본문에서 파일명이 참조돼야 한다
        if usage in ("codegen", "hybrid") and gen_src:
            if fp.name not in gen_src:
                violations.append(
                    f"{fp.name}  _usage={usage} 인데 gen_constants.py 에서 "
                    f"`{fp.name}` 미참조 — load_schemas() 추가 또는 _usage 변경 필요")
    return violations


def check_strategy_pattern_consistency() -> list[str]:
    """전략코드 패턴 정합 가드 (사냥꾼 라운드 M6, 2026-06-08).

    - common.json $defs.StrategyPattern.pattern == STRATEGY_PATTERN_EXPECTED
      (gen_constants.py 가 common.json 에서 파생하므로 이 둘이 일치해야 생성물도 일치)
    - ems_strategies.json 의 모든 전략 코드가 그 패턴에 매칭 (codes ↔ pattern drift 가드)
    """
    violations: list[str] = []
    try:
        common = json.loads((SCHEMAS_DIR / "common.json").read_text(encoding="utf-8"))
        ems = json.loads((SCHEMAS_DIR / "ems_strategies.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [f"strategy pattern 정합 검사 로드 실패: {e}"]
    pat = common.get("$defs", {}).get("StrategyPattern", {}).get("pattern")
    if pat is None:
        return ["common.json $defs.StrategyPattern.pattern 누락"]
    if pat != STRATEGY_PATTERN_EXPECTED:
        violations.append(
            f"common.json StrategyPattern.pattern={pat!r} != 기대값 "
            f"{STRATEGY_PATTERN_EXPECTED!r} — gen/validate 정합이 깨짐")
    try:
        rx = re.compile(pat)
    except re.error as e:
        return [f"StrategyPattern 정규식 컴파일 실패: {e}"]
    codes = list(ems.get("default", {}).get("strategies", {}).keys())
    for c in codes:
        if not rx.fullmatch(c):
            violations.append(
                f"ems_strategies code {c!r} 가 StrategyPattern {pat!r} 에 불일치")
    return violations


def check_index_completeness() -> list[str]:
    """_index.yaml 카탈로그가 schemas/*.json 전수를 등재했는지 (사냥꾼 라운드 LOW, 2026-06-08).

    기존엔 58 schema 중 31 만 등재돼 Redocly/Swagger 렌더링 시 절반이 누락됐다.
    entry 수 == .json 파일 수 + phantom(존재하지 않는 schema 참조) 0 을 강제한다.
    """
    idx = SCHEMAS_DIR / "_index.yaml"
    if not idx.exists():
        return []
    text = idx.read_text(encoding="utf-8")
    referenced = set(re.findall(r"\$ref:\s*'([^']+\.json)'", text))
    actual = {p.name for p in SCHEMAS_DIR.glob("*.json")}
    violations: list[str] = []
    for m in sorted(actual - referenced):
        violations.append(f"_index.yaml  {m} 미등재 — schemas/*.json 전수 등재 필요")
    for p in sorted(referenced - actual):
        violations.append(f"_index.yaml  {p} phantom entry — 존재하지 않는 schema 참조")
    return violations


def check_codegen_input_usage() -> list[str]:
    """역방향 가드 (Deferred D-1, 사냥꾼 M4) — gen_constants.py 가 로드하는 schema 는
    반드시 `_usage ∈ {codegen, hybrid}` 여야 한다.

    `check_schema_usage_headers()` 는 정방향(codegen/hybrid → gen 참조)만 검사한다.
    그 단방향만으로는 'gen 이 실제로 로드하지만 _usage=runtime-validate' 로 잘못
    선언된 schema(esg_policy / dr_dispatch_event)를 잡지 못했다. 본 가드는
    load_schemas() 본문에서 참조하는 모든 schema 파일명을 추출해 _usage 를 역검증한다.
    감사(2026-06-08): 본 가드는 esg_policy/dr_dispatch_event 2건 외 false-positive 0.
    """
    gen_fp = CONTRACTS_ROOT / "scripts" / "gen_constants.py"
    if not gen_fp.exists():
        return []
    gen_src = gen_fp.read_text(encoding="utf-8")
    m = re.search(r"def load_schemas\(\).*?(?=\ndef )", gen_src, re.S)
    if not m:
        return ["gen_constants.py load_schemas() 본문 추출 실패 — 역방향 usage 검사 불가"]
    body = m.group(0)
    referenced = sorted(set(re.findall(r'"([a-z0-9_]+\.json)"', body)))
    violations: list[str] = []
    for name in referenced:
        fp = SCHEMAS_DIR / name
        if not fp.exists():
            continue
        try:
            usage = json.loads(fp.read_text(encoding="utf-8")).get("_usage")
        except Exception as e:
            violations.append(f"{name}  JSON 파싱 실패: {e}")
            continue
        if usage not in ("codegen", "hybrid"):
            violations.append(
                f"{name}  gen_constants.load_schemas() 가 로드하나 "
                f"_usage={usage!r} — codegen 입력은 _usage ∈ {{codegen, hybrid}} 필수")
    return violations


def check_legacy_code_consistency() -> list[str]:
    """legacy E-code 교차 정합 가드 (Deferred D-2, 사냥꾼 M7).

    `ems_strategies.json#default.legacy_mapping.gcs_e_codes` 와 전용 drift-guard SSOT
    `legacy_ems_code_mapping.json#deprecated_e_codes[*].maps_to` 가 같은 E-code 에서
    동일 M-code 를 가리켜야 한다. 정본은 legacy_ems_code_mapping.json (drift_note 근거 보유).
    두 파일에 공통 존재하는 E-code 만 비교한다(부분집합 허용).
    """
    try:
        ems = json.loads((SCHEMAS_DIR / "ems_strategies.json").read_text(encoding="utf-8"))
        legacy = json.loads(
            (SCHEMAS_DIR / "legacy_ems_code_mapping.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [f"legacy code 정합 검사 로드 실패: {e}"]
    gcs = ems.get("default", {}).get("legacy_mapping", {}).get("gcs_e_codes", {})
    authoritative = legacy.get("deprecated_e_codes", {})
    violations: list[str] = []
    for ecode, mcode in sorted(gcs.items()):
        auth_entry = authoritative.get(ecode)
        if not isinstance(auth_entry, dict):
            continue  # 정본에 없는 E-code 는 비교 대상 아님
        auth_m = auth_entry.get("maps_to")
        if auth_m is not None and mcode != auth_m:
            violations.append(
                f"ems_strategies gcs_e_codes[{ecode}]={mcode} != "
                f"legacy_ems_code_mapping.deprecated_e_codes[{ecode}].maps_to={auth_m} "
                f"(정본=legacy_ems_code_mapping.json)")
    return violations


def check_mirror_core_keywords() -> list[str]:
    """20 BASE CORE_KEYWORDS 로컬 검증 가드 (Deferred D-3, 사냥꾼 LOW).

    CLAUDE.md mirror 헤더가 ai-champion-2026 verifier(`verify_cross_folder_mirror_drift.py`
    #BASE_KEYWORDS)가 요구하는 20 키워드를 실제로 보유하는지 본 repo 단독으로 검증한다.
    (기존엔 verifier 가 sibling 에만 있어 로컬 검증 불가 = D-3.)

    검사:
      1. `<!-- MIRROR_CORE_KEYWORDS_BASE_V1 -->` ~ `<!-- /... -->` enumeration 블록 추출
      2. backtick 토큰 파싱 → 정확히 20 개여야 함
      3. enumeration 블록을 **제외한** mirror 영역(헤더 + 50 라인) 본문에 각 토큰이
         전수 등장해야 함 — enumeration 만 있고 prose 가 stale 한 경우를 잡는다.

    cross-folder 동기(enumeration ↔ BASE_KEYWORDS 동일 집합)는 ai-champion-2026 verifier 가 강제.
    """
    fp = CONTRACTS_ROOT / "CLAUDE.md"
    if not fp.exists():
        return ["CLAUDE.md 미발견 — mirror CORE_KEYWORDS 검증 불가"]
    text = fp.read_text(encoding="utf-8")
    block_re = re.compile(
        r"<!--\s*MIRROR_CORE_KEYWORDS_BASE_V1\s*-->(.*?)<!--\s*/MIRROR_CORE_KEYWORDS_BASE_V1\s*-->",
        re.S)
    m = block_re.search(text)
    if not m:
        return ["CLAUDE.md  MIRROR_CORE_KEYWORDS_BASE_V1 enumeration 블록 부재 (D-3 — 로컬 검증 불가)"]
    block = m.group(1)
    keywords = re.findall(r"`([^`]+)`", block)
    violations: list[str] = []
    if len(keywords) != 20:
        violations.append(
            f"CLAUDE.md  BASE CORE_KEYWORDS enumeration 개수={len(keywords)} (기대 20) "
            f"— ai-champion-2026 BASE_KEYWORDS 와 동기 필요")
    # enumeration 블록을 제외한 mirror 영역 본문 추출
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if re.search(r"^>\s*\*\*SSOT\*\*:\s*ai_core", ln)), None)
    if start is None:
        return ["CLAUDE.md  mirror 헤더(`> **SSOT**: ai_core`) 미발견 — 영역 검증 불가"]
    region = "\n".join(lines[start:start + 50])
    prose = block_re.sub("", region)  # 자기참조 enumeration 제거
    for kw in keywords:
        if kw not in prose:
            violations.append(
                f"CLAUDE.md  CORE_KEYWORD `{kw}` 가 enumeration 에는 있으나 "
                f"mirror 헤더 본문에 부재 — prose stale (헤더 보강 필요)")
    return violations


# ── EC pin lockstep (P1, 2026-06-17 skew 재발 방지) ──────────────────────────

# energy-contracts 를 git+https 로 pin 하는 consumer (lockstep 그룹).
# 이번 사고: gridbridge/edge-agent 가 pin v0.2.4(M00~M15) 인데 _generated_constants 는
# M00~M20 으로 regen → CI 에서만 jsonschema 가 M19/M20 거부. be-3d 는 v0.3.6 으로 divergent.
EC_PIN_CONSUMERS = ("edge-agent", "gridbridge", "building-energy-3d")
_EC_PIN_RE = re.compile(r"energy-contracts.*?@(v[0-9][\w.\-]*)")
_GEN_CONST_RELPATHS = (
    "src/_generated_constants.py", "_generated_constants.py",
    "src/shared/_generated_constants.py", "backend/_generated_constants.py",
)


def _ec_pin(repo: Path) -> str | None:
    pp = repo / "pyproject.toml"
    if not pp.exists():
        return None
    m = _EC_PIN_RE.search(pp.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _gen_const_file(repo: Path) -> Path | None:
    for rel in _GEN_CONST_RELPATHS:
        if (repo / rel).exists():
            return repo / rel
    return None


def _clean_git_env() -> dict:
    """상속된 GIT_* 환경변수 제거. consumer(be-3d 등)의 pre-commit 훅이 export 한
    GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE 등이 `git -C {CONTRACTS_ROOT}` 의 `-C` 를
    무력화(호출 repo 를 봄) → energy-contracts 태그 조회가 엉뚱한 repo 에서 실패한다
    (2026-06-18 실측 근본원인: be-3d 미러 커밋 시 GIT_DIR=be-3d 누수 → 'tag 조회 실패').
    GIT_* 를 벗겨 `-C` 가 정확히 energy-contracts 를 가리키게 한다."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git_show_at_tag(tag: str, path: str) -> str | None:
    """`git show {tag}:{path}` blob 반환. 태그가 로컬에 없으면(`git show` 실패) 해당
    태그만 1회 targeted fetch 후 재시도(self-heal). 정상 경로(태그 존재)엔 네트워크 0.
    오프라인이거나 태그 자체가 부재하면 None → 호출부 soft-skip.

    배경(2026-06-18): consumer 미러 커밋 시 ① 로컬 energy-contracts 에 pin 태그 부재 →
      매번 수동 `fetch --tags` + `--no-verify` 강제(self-heal 로 해소), ② 더 근본은 git 훅이
      export 한 GIT_DIR 누수가 `-C` 를 무력화 → 엉뚱한 repo 조회 실패(_clean_git_env 로 해소).
      두 경로 모두 GIT_* 벗긴 env 로 호출."""
    ref = f"{tag}:{path}"
    env = _clean_git_env()

    def _show() -> str | None:
        try:
            return subprocess.check_output(
                ["git", "-C", str(CONTRACTS_ROOT), "show", ref],
                text=True, encoding="utf-8", stderr=subprocess.DEVNULL, env=env)
        except Exception:
            return None

    blob = _show()
    if blob is not None:
        return blob
    # 태그 로컬 부재 가능 → 해당 태그만 targeted fetch(빠름) 후 1회 재시도.
    try:
        subprocess.run(
            ["git", "-C", str(CONTRACTS_ROOT), "fetch", "--quiet", "origin", "tag", tag],
            check=True, timeout=30, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return None  # 오프라인/원격 없음 → soft-skip
    return _show()


def check_ec_pin_lockstep() -> list[str]:
    """energy-contracts pin lockstep + 커밋 constants ⊆ pin 태그 enum 가드.

    2026-06-17 skew 재발 방지. 세 가지를 커밋 시점에 차단:
      1) 전 consumer pin 동일 (divergent pin = gridbridge/edge-agent v0.2.4 ≠ be-3d v0.3.6 유형)
      2) 커밋된 STRATEGY_CODES ⊆ pin 태그의 control_command enum
         (regen 은 M19/M20 인데 pin 태그 schema 는 M15 상한 = CI-only 실패 유형)
      3) consumer 간 SOURCE_HASH 동일 (부분 regen 방지)
    """
    proj = WORKSPACE_ROOT / "projects"
    pins: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for name in EC_PIN_CONSUMERS:
        repo = proj / name
        if not repo.exists():
            continue
        pin = _ec_pin(repo)
        if pin:
            pins[name] = pin
        gc = _gen_const_file(repo)
        if gc:
            m = re.search(r'SOURCE_HASH\s*=\s*"([0-9a-f]+)"', gc.read_text(encoding="utf-8"))
            if m:
                hashes[name] = m.group(1)

    violations: list[str] = []
    distinct_pins = set(pins.values())
    if len(distinct_pins) > 1:
        violations.append(
            f"energy-contracts pin lockstep 위반: {pins} — 전 consumer 동일 태그 필요 "
            f"(scripts/bump_ec_pin.py 로 일괄 bump)")
    distinct_hashes = set(hashes.values())
    if len(distinct_hashes) > 1:
        violations.append(
            f"_generated_constants SOURCE_HASH 불일치(부분 regen): {hashes} — gen_constants.py --all 재실행")

    # pin 태그 enum 커버리지 (단일 pin 일 때만)
    if len(distinct_pins) == 1:
        pin = next(iter(distinct_pins))
        enum: set[str] | None = None
        # 태그 미존재 시 self-heal(targeted fetch). 오프라인·태그 부재면 None → soft-skip.
        blob = _git_show_at_tag(pin, "energy_contracts/schemas/control_command.json")
        if blob is None:
            violations.append(
                f"pin 태그 {pin} control_command.json 조회 실패(오프라인이거나 원격에 태그 부재) — "
                f"온라인에서 `git -C projects/energy-contracts fetch --tags origin` 후 재시도 (커버리지 검증 skip)")
        else:
            try:
                enum = set(json.loads(blob).get("properties", {})
                           .get("strategy", {}).get("enum", []))
            except Exception:
                violations.append(f"pin 태그 {pin} control_command.json 파싱 실패 (커버리지 검증 skip)")
        if enum:
            for name in EC_PIN_CONSUMERS:
                gc = _gen_const_file(proj / name)
                if not gc:
                    continue
                m = re.search(r"STRATEGY_CODES[^=]*=\s*\[(.*?)\]",
                              gc.read_text(encoding="utf-8"), re.S)
                codes = set(re.findall(r"M\d{2}", m.group(1))) if m else set()
                missing = sorted(codes - enum)
                if missing:
                    violations.append(
                        f"{name}: 커밋된 STRATEGY_CODES {missing} 가 pin 태그 {pin} 의 "
                        f"control_command enum 에 없음 — pin 을 bump 하거나 regen 을 되돌릴 것 "
                        f"(2026-06-17 M19/M20 skew 유형, CI 에서만 터지던 회귀)")
    return violations


# ── 로컬 mirror drift (P3, 2026-06-17) ───────────────────────────────────────

def _load_mirror_verifier():
    """ai-champion-2026 의 verify_cross_folder_mirror_drift 를 import (키워드 SSOT 단일화).

    키워드를 본 파일에 복제하지 않고 verifier 에서 직접 읽어 drift 를 원천 차단.
    verifier 부재(클론 없음) 시 None → soft-skip.
    """
    import importlib.util
    base = WORKSPACE_ROOT / "공모전"
    cands = list(base.glob("*/scripts/verify_cross_folder_mirror_drift.py")) if base.exists() else []
    if not cands:
        return None
    spec = importlib.util.spec_from_file_location("driftv_local", cands[0])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["driftv_local"] = mod  # dataclass introspection 위해 등록 필수
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def check_local_mirror_drift() -> list[str]:
    """커밋 대상 repo 의 CLAUDE.md mirror 헤더가 요구 키워드(BASE + REVERSE 거점이면 REVERSE)를
    보유하는지 로컬 검증 (P3). 2026-06-17 be-3d 가 REVERSE 5/8 → ratio 0.89 로 ai-champion CI
    에서만 터지던 drift 를 push 전에 차단. 키워드 SSOT = ai-champion verifier (복제 없음).
    """
    mod = _load_mirror_verifier()
    if mod is None:
        return []  # verifier 미존재 — soft-skip (CI ai-champion 게이트가 authoritative)
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8").strip())
    except Exception:
        return []
    repo_name = repo_root.name
    fp = repo_root / "CLAUDE.md"
    if not fp.exists():
        return []
    try:
        required = mod._required_keywords(repo_name)  # BASE(+REVERSE if REVERSE_SIBLING)
        threshold = 0.90
    except Exception:
        return []
    text = fp.read_text(encoding="utf-8", errors="replace")
    matched = [k for k in required if k in text]
    ratio = len(matched) / max(1, len(required))
    if ratio < threshold:
        missing = [k for k in required if k not in text]
        return [f"CLAUDE.md mirror drift: {repo_name} 키워드 {len(matched)}/{len(required)} "
                f"(ratio {ratio:.2f} < {threshold}) — 누락 {missing} "
                f"(ai-champion cross-folder-drift-verify 게이트 사전 차단)"]
    return []


# ── 변경 파일 (pre-commit) ───────────────────────────────────────────────────

def changed_files() -> list[Path]:
    """git diff --cached --name-only 결과. CWD = pre-commit이 실행된 git repo 루트."""
    try:
        # 현재 작업 디렉토리의 git repo 루트를 찾음
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, encoding="utf-8").strip())
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(repo_root), text=True, encoding="utf-8")
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        p = repo_root / line
        if p.exists():
            files.append(p)
    return files


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check",
                    choices=["strategy", "ports", "schemas", "generated",
                             "usage", "all"],
                    default="all")
    ap.add_argument("--pre-commit", action="store_true",
                    help="git diff --cached 대상만 검사")
    ap.add_argument("paths", nargs="*", help="검사할 경로 (기본: 워크스페이스 주요 프로젝트)")
    args = ap.parse_args()

    if args.paths:
        paths = [Path(p).resolve() for p in args.paths]
    elif args.pre_commit:
        paths = changed_files()
        if not paths:
            print("[SSOT] 변경 파일 없음, 통과")
            return 0
    else:
        # 기본 검사 대상
        paths = [
            WORKSPACE_ROOT / "projects" / p for p in
            ("edge-agent", "gridbridge", "building-energy-3d",
             "agentleague", "eduarena", "energy-contracts")
        ]
        paths = [p for p in paths if p.exists()]

    failed = False
    total_violations = 0

    if args.check in ("strategy", "all"):
        v = scan_legacy_strategies(paths)
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 구 전략 코드(M0~M8 단독) 발견: {len(v)}건")
            for fp, ln, snippet in v[:30]:
                rel = fp.relative_to(WORKSPACE_ROOT) if fp.is_absolute() else fp
                print(f"  {rel}:{ln}  {snippet}")
            if len(v) > 30:
                print(f"  ... 외 {len(v)-30}건 (총 {len(v)})")

    if args.check in ("ports", "all"):
        v = check_port_conflicts()
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 포트 충돌: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if args.check in ("schemas", "all"):
        v = check_schema_strategy_patterns()
        v += check_strategy_pattern_consistency()  # 사냥꾼 M6
        v += check_index_completeness()            # 사냥꾼 LOW — _index.yaml 전수 등재
        v += check_legacy_code_consistency()       # Deferred D-2 (M7) — E-code 교차 정합
        v += check_mirror_core_keywords()          # Deferred D-3 — 20 BASE CORE_KEYWORDS 로컬 검증
        v += check_local_mirror_drift()            # P3 (2026-06-17) — 커밋 repo CLAUDE.md REVERSE 키워드 로컬 가드
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] 스키마 패턴 위반: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if args.check in ("generated", "all"):
        v = check_generated_drift()
        v += check_ec_pin_lockstep()               # P1 (2026-06-17) — EC pin↔regen skew 차단
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] _generated_constants drift: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if args.check in ("usage", "all"):
        v = check_schema_usage_headers()
        v += check_codegen_input_usage()           # Deferred D-1 (M4) — 역방향 usage 가드
        if v:
            failed = True
            total_violations += len(v)
            print(f"\n[SSOT] schema _usage 헤더 위반: {len(v)}건")
            for line in v:
                print(f"  {line}")

    if failed:
        print(f"\n[SSOT] 위반 총 {total_violations}건 — 커밋 차단")
        return 1
    print("[SSOT] 모든 검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
