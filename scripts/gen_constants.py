"""JSON Schema → Python/TypeScript 상수 자동 생성기.

Tier 2 (energy-contracts/schemas/*.json) → Tier 3 (각 프로젝트/_generated_constants.{py,ts}).

생성 산출물:
  - STRATEGIES        — M00~M15 전략 메타 (name_en, name_kr, type, components)
  - STRATEGY_CODES    — list[str]
  - STRATEGY_PATTERN  — regex
  - SIGNAL_MAPPING    — DR signal → strategy
  - LEGACY_MAPPING    — 구 코드 → 통일 코드 (읽기 전용)
  - PORTS             — 포트 번호 상수 (port_allocation.json)

사용법:
  python gen_constants.py --target python --out ../edge-agent/src/_generated_constants.py
  python gen_constants.py --target ts --out ../building-energy-3d/frontend/src/shared/_generated_constants.ts
  python gen_constants.py --target python --out edge-agent  # 프로젝트명만 — 표준 경로
  python gen_constants.py --check                          # 모든 등록 프로젝트 일관성 검사 (CI용)
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = CONTRACTS_ROOT / "schemas"
WORKSPACE_ROOT = CONTRACTS_ROOT.parents[1]

# 표준 프로젝트별 출력 경로 (Tier 3) — Phase M-4: exports 화이트리스트 도입
#
# 각 프로젝트 항목 구조:
#   {
#     "python":  "<path>",                # Python 산출물 경로 (선택)
#     "ts":      "<path>",                # TypeScript 산출물 경로 (선택)
#     "exports": {"python": [...],        # Python 본문에서 keep 할 심볼
#                 "ts":     [...]},       # TS 본문에서 keep 할 심볼
#   }
# `exports` 누락 시 전체 emit (backward compatible). 화이트리스트 외 symbol 은
# 생성물에서 제거되어 dead-export 가 줄어든다 (M-4 H9 해결).
#
# 화이트리스트 → m4_survey_exports.py 산출 (`scratch/m4_exports_audit.json`)
# 기반으로 결정. 새 symbol 필요 시 본 manifest 갱신 후 `--all` 재실행.
PROJECT_TARGETS: dict[str, dict] = {
    "edge-agent": {
        "python": "projects/edge-agent/src/_generated_constants.py",
        "exports": {
            "python": [
                "AI_MODELS", "AUTH_JWT_POLICY", "AUTH_PROJECT_DEFAULT_SCOPES",
                "BUILDING_USAGES", "COMPUTER_PROFILES", "DATA_SOURCES",
                "DATA_SOURCE_LABELS", "DB_MIGRATIONS", "ENERGY_CONVERSIONS",
                "DISPATCH_SOURCES", "DISPATCH_STATUSES",
                "ERROR_CODES", "GRIDBRIDGE_URL_COMPUTER_A",
                "GRIDBRIDGE_URL_DEFAULT", "I18N_KEYS", "INTENT_TYPES",
                "LEGACY_MAPPING", "LINT_CONFIG", "LOGGING_FORMAT",
                "MQTT_TOPIC_PATTERNS", "OPENAPI_RESPONSES", "PIPELINE_DATASETS",
                "PORTS", "RUN_MODES", "RUN_MODE_BEHAVIOR", "SECURITY_HEADERS",
                "SIGNAL_MAPPING", "SIGNAL_MAPPING_DR",
                "SIM_EMS_PATTERNS", "STRATEGIES",
                "STRATEGY_CODES", "STRATEGY_PATTERN", "TENANT_REGIONS",
                "TESTS_SHARED", "TEST_GROUPS", "TEST_STAGES", "TEST_TIERS",
            ],
        },
    },
    "gridbridge": {
        "python": "projects/gridbridge/src/_generated_constants.py",
        "exports": {
            "python": [
                "AI_MODELS", "AUTH_JWT_POLICY", "AUTH_SCOPES",
                "BID_STRATEGIES", "COMPUTER_PROFILES",
                "DATA_SOURCES", "DATA_SOURCE_LABELS", "DB_MIGRATIONS",
                "DISPATCH_SOURCES", "DISPATCH_STATUSES",
                "DISTRIBUTION_ALGORITHMS", "DR_TYPES",
                "EMISSION_FACTORS_KR", "ENERGY_CONVERSIONS", "ERROR_CODES",
                "GRIDBRIDGE_URL_COMPUTER_A", "LOGGING_FORMAT",
                "MANAGEMENT_MODES", "MQTT_TOPIC_PATTERNS",
                "OPENAPI_RESPONSES", "PIPELINE_DATASETS", "PORTS",
                "RUN_MODES", "RUN_MODE_BEHAVIOR", "SECURITY_HEADERS",
                "SIGNAL_MAPPING", "SIGNAL_MAPPING_DR",
                "SIM_EMS_PATTERNS", "STRATEGY_CODES",
                "STRATEGY_PATTERN", "TENANT_REGIONS", "TESTS_SHARED",
                "TEST_GROUPS", "TEST_STAGES", "TEST_TIERS",
            ],
        },
    },
    "building-energy-3d": {
        "python": "projects/building-energy-3d/src/shared/_generated_constants.py",
        "ts":     "projects/building-energy-3d/frontend/src/shared/_generated_constants.ts",
        "exports": {
            "python": [
                "AGENT_REGISTRY", "AI_MODELS", "AUTH_JWT_POLICY", "AUTH_PERMISSIONS",
                "AUTH_PROJECT_DEFAULT_SCOPES", "AUTH_SCOPES",
                "BID_STRATEGIES", "BUILDING_USAGES",
                "COMPUTER_PROFILES", "DATA_SOURCES", "DATA_SOURCE_LABELS",
                "DB_MIGRATIONS", "DISPATCH_SOURCES", "DISPATCH_STATUSES",
                "DISTRIBUTION_ALGORITHMS", "DR_TYPES",
                "EMISSION_FACTORS_KR", "ENERGY_CONVERSIONS",
                "ERROR_CODES", "ERROR_TYPE_PREFIX", "I18N_FALLBACK_LANG",
                "I18N_KEYS", "INTENT_TYPES", "LINT_CONFIG", "LOGGING_FORMAT",
                "MANAGEMENT_MODES", "MQTT_NAMESPACES", "MQTT_TOPIC_PATTERNS",
                "NL_CONSTRAINTS",
                "NL_CONTROL_KEYWORDS", "NL_GATE_TOKENS", "NL_STRATEGIES_BY_KEYWORD",
                "OPENAPI_RESPONSES", "PIPELINE_DATASETS", "PRIMARY_ENERGY_FACTORS",
                "RUN_MODES", "RUN_MODE_BEHAVIOR", "SECURITY_CORS", "SECURITY_HEADERS",
                "SIGNAL_MAPPING_DR",
                "SIM_EMS_PATTERNS", "SIM_PMV_THRESHOLDS", "SIM_RUN_PERIODS",
                "STRATEGIES", "STRATEGY_CODES", "TENANT_REGIONS", "TESTS_SHARED",
                "TEST_GROUPS", "TEST_STAGES", "TEST_TIERS", "ZEB_THRESHOLDS",
            ],
            "ts": [
                "I18N_FALLBACK_LANG", "I18N_KEYS",
            ],
        },
    },
    "agentleague": {
        "python": "projects/agentleague/backend/_generated_constants.py",
        "exports": {
            "python": [
                "AI_MODELS", "AUTH_JWT_POLICY", "AUTH_PROJECT_DEFAULT_SCOPES",
                "AUTH_SCOPES", "BUILDING_USAGES", "COMPUTER_PROFILES",
                "DATA_SOURCE_LABELS", "ENERGY_CONVERSIONS", "ERROR_CODES",
                "GRIDBRIDGE_URL_COMPUTER_A", "GRIDBRIDGE_URL_DEFAULT",
                "I18N_KEYS", "LOGGING_FORMAT", "MQTT_NAMESPACES",
                "OPENAPI_RESPONSES", "PIPELINE_DATASETS", "RUN_MODES",
                "RUN_MODE_BEHAVIOR", "SECURITY_CORS", "SECURITY_HEADERS",
                "STRATEGIES", "STRATEGY_CODES", "STRATEGY_PATTERN",
                "TENANT_REGIONS", "TESTS_SHARED", "TEST_STAGES", "TEST_TIERS",
            ],
        },
    },
    "eduarena": {
        "python": "projects/eduarena/backend/_generated_constants.py",
        "exports": {
            "python": [
                "AI_MODELS", "AUTH_JWT_POLICY", "AUTH_PROJECT_DEFAULT_SCOPES",
                "AUTH_SCOPES", "BUILDING_USAGES", "COMPUTER_PROFILES",
                "DATA_SOURCE_LABELS", "ENERGY_CONVERSIONS", "ERROR_CODES",
                "GRIDBRIDGE_URL_COMPUTER_A", "GRIDBRIDGE_URL_DEFAULT",
                "I18N_KEYS", "LOGGING_FORMAT", "MQTT_NAMESPACES",
                "OPENAPI_RESPONSES", "PIPELINE_DATASETS", "RUN_MODES",
                "RUN_MODE_BEHAVIOR", "SECURITY_HEADERS", "STRATEGIES",
                "STRATEGY_CODES", "STRATEGY_PATTERN", "TENANT_REGIONS",
                "TESTS_SHARED", "TEST_STAGES", "TEST_TIERS", "ZEB_THRESHOLDS",
            ],
        },
    },
}


def load_schemas() -> dict:
    """필요한 SSOT 스키마들을 로드해 단일 dict로 반환."""
    ems = json.loads((SCHEMAS_DIR / "ems_strategies.json").read_text(encoding="utf-8"))
    ports = json.loads((SCHEMAS_DIR / "port_allocation.json").read_text(encoding="utf-8"))
    common = json.loads((SCHEMAS_DIR / "common.json").read_text(encoding="utf-8"))
    # Phase C 신규
    agents_fp = SCHEMAS_DIR / "agent_contracts.json"
    intents_fp = SCHEMAS_DIR / "nl_intents.json"
    agents = json.loads(agents_fp.read_text(encoding="utf-8")) if agents_fp.exists() else {}
    intents = json.loads(intents_fp.read_text(encoding="utf-8")) if intents_fp.exists() else {}
    # Phase E/F/G 신규
    modes_fp = SCHEMAS_DIR / "run_modes.json"
    data_fp = SCHEMAS_DIR / "data_classification.json"
    tests_fp = SCHEMAS_DIR / "test_classification.json"
    modes = json.loads(modes_fp.read_text(encoding="utf-8")) if modes_fp.exists() else {}
    dataclass = json.loads(data_fp.read_text(encoding="utf-8")) if data_fp.exists() else {}
    tests = json.loads(tests_fp.read_text(encoding="utf-8")) if tests_fp.exists() else {}
    # Phase I 신규 (5개 SSOT)
    def _load(name: str) -> dict:
        fp = SCHEMAS_DIR / name
        return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    models = _load("ai_model_registry.json")
    auth = _load("auth_scopes.json")
    errors = _load("error_response.json")
    mqtt = _load("mqtt_topics.json")
    security = _load("security_policy.json")
    # Phase J 신규 (7개)
    cmpprof = _load("computer_profile.json")
    usage = _load("building_usage_map.json")
    i18n = _load("i18n_keys.json")
    tenant_reg = _load("tenant_regions.json")
    authpol = _load("auth_policy.json")
    pipeline = _load("pipeline_status.json")
    units = _load("energy_units.json")
    # Phase K 신규 (6개)
    tests_shared = _load("tests_shared.json")
    logfmt = _load("logging_format.json")
    sim_scn = _load("simulation_scenarios.json")
    dbmig = _load("db_migrations.json")
    oapi_resp = _load("openapi_responses.json")
    lintfmt = _load("lint_format.json")
    # Phase L 신규 (2개 — AI 챔피언 Phase 4 DR Aggregator)
    esg_policy = _load("esg_policy.json")
    dr_dispatch = _load("dr_dispatch_event.json")
    return {"ems": ems, "ports": ports, "common": common,
            "agents": agents, "intents": intents,
            "modes": modes, "dataclass": dataclass, "tests": tests,
            "models": models, "auth": auth, "errors": errors,
            "mqtt": mqtt, "security": security,
            "cmpprof": cmpprof, "usage": usage, "i18n": i18n,
            "tenant_reg": tenant_reg, "authpol": authpol,
            "pipeline": pipeline, "units": units,
            "tests_shared": tests_shared, "logfmt": logfmt,
            "sim_scn": sim_scn, "dbmig": dbmig,
            "oapi_resp": oapi_resp, "lintfmt": lintfmt,
            "esg_policy": esg_policy, "dr_dispatch": dr_dispatch}


def schemas_hash(data: dict) -> str:
    """소스 스키마 + 생성기 본체 의 SHA-256 해시 — 변경 감지용.

    Phase H 보강(M7): schemas 무변경이지만 gen_constants.py 자체 알고리즘이
    바뀌어도 hash가 갱신되어 "위장 통과(silent drift)" 방지. 자기 자신을
    bytes 로 읽어 schemas dict 와 함께 해시.

    Phase 4 H11 fix: read_text() + encode() 로 newline 정규화 — Windows(CRLF)
    와 Linux(LF) 사이 hash 불일치 차단 (서버측 CI 와 로컬 일치 보장).
    """
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    try:
        self_bytes = Path(__file__).read_text(encoding="utf-8").encode("utf-8")
    except Exception:
        self_bytes = b""
    h = hashlib.sha256()
    h.update(blob)
    h.update(b"\x00gen_constants_self\x00")
    h.update(self_bytes)
    return h.hexdigest()[:16]


# ── Python 생성 ──────────────────────────────────────────────────────────────

PY_HEADER = '''"""AUTO-GENERATED constants from energy-contracts/schemas/.

DO NOT EDIT. Run `python energy-contracts/scripts/gen_constants.py` to regenerate.

Source SSOT: energy-contracts/schemas/ems_strategies.json, port_allocation.json, common.json
Generated by: gen_constants.py (myjob/docs/SSOT_GOVERNANCE.md Phase B)
Source hash: {hash}
"""
from __future__ import annotations

SOURCE_HASH = "{hash}"
'''


def _find_service_port(ports: dict, service_name: str, fallback: int) -> int:
    """port_allocation.json services 에서 이름으로 포트 조회. 미발견 시 fallback."""
    for svc in ports.get("services", []):
        if svc.get("name") == service_name and isinstance(svc.get("port"), int):
            return svc["port"]
    return fallback


def gen_python(schemas: dict) -> str:
    h = schemas_hash(schemas)
    ems = schemas["ems"]["default"]
    ports = schemas["ports"]

    lines = [PY_HEADER.format(hash=h)]

    # Strategy codes
    codes = list(ems["strategies"].keys())
    lines.append("")
    lines.append("# ─ Strategy codes ────────────────────────────────────────────")
    lines.append(f"STRATEGY_CODES: list[str] = {codes!r}")
    lines.append(f'STRATEGY_PATTERN: str = r"^M(0[0-9]|1[0-5])$"')
    lines.append("")

    # Strategies dict
    lines.append("STRATEGIES: dict[str, dict] = {")
    for code, meta in ems["strategies"].items():
        lines.append(f"    {code!r}: {meta!r},")
    lines.append("}")
    lines.append("")

    # Signal mapping
    lines.append("# ─ DR signal → strategy ─────────────────────────────────────")
    lines.append(f"SIGNAL_MAPPING: dict[str, str] = {ems['signal_mapping']!r}")
    lines.append("")

    # Phase 4 — signal_mapping_dr (dr_type 분기)
    if "signal_mapping_dr" in ems:
        lines.append("# ─ Phase 4 — DR signal → strategy, dr_type 분기 ─────────────")
        lines.append(f"SIGNAL_MAPPING_DR: dict[str, dict[str, str]] = {ems['signal_mapping_dr']!r}")
        lines.append("")

    # Phase 4 — DR Aggregator enums (esg_policy.json + dr_dispatch_event.json)
    esg = schemas.get("esg_policy") or {}
    dispatch = schemas.get("dr_dispatch") or {}
    if esg:
        lines.append("# ─ Phase 4 — ESG Aggregator enums ───────────────────────────")
        for name, ref in [
            ("DR_TYPES",              esg.get("$defs", {}).get("DRType", {}).get("enum")),
            ("MANAGEMENT_MODES",      esg.get("$defs", {}).get("ManagementMode", {}).get("enum")),
            ("BID_STRATEGIES",        esg.get("$defs", {}).get("BidStrategy", {}).get("enum")),
            ("DISTRIBUTION_ALGORITHMS", esg.get("$defs", {}).get("DistributionAlgorithm", {}).get("enum")),
        ]:
            if ref:
                lines.append(f"{name}: list[str] = {ref!r}")
        lines.append("")
    if dispatch:
        for name, ref in [
            ("DISPATCH_SOURCES",  dispatch.get("$defs", {}).get("DispatchSource", {}).get("enum")),
            ("DISPATCH_STATUSES", dispatch.get("$defs", {}).get("DispatchStatus", {}).get("enum")),
        ]:
            if ref:
                lines.append(f"{name}: list[str] = {ref!r}")
        lines.append("")

    # Legacy mapping (lookup only)
    lines.append("# ─ Legacy code mapping (lookup only — DO NOT use for new code) ─")
    lines.append(f"LEGACY_MAPPING: dict[str, dict[str, str]] = {ems['legacy_mapping']!r}")
    lines.append("")

    # Ports
    lines.append("# ─ Port allocation (Tier 1 SSOT) ────────────────────────────")
    lines.append("PORTS: dict[str, int] = {")
    for svc in ports.get("services", []):
        if "port" not in svc:
            continue
        # 키 변환: "GridBridge (Computer A canonical)" → "GRIDBRIDGE_A"
        key = re.sub(r"[^A-Za-z0-9]+", "_", svc["name"]).strip("_").upper()
        lines.append(f"    {key!r}: {svc['port']},")
    lines.append("}")
    lines.append("")

    # Computer A 특수 포트 (자주 쓰임). URL 은 services 의 GridBridge 항목에서 동적 추출.
    lines.append("# ─ Computer A override (Docker가 8001/8002 점유) ────────────")
    machine_a = ports.get("machines", {}).get("A", {})
    default_port = _find_service_port(ports, "GridBridge (code default)", 8001)
    computer_a_port = _find_service_port(ports, "GridBridge (Computer A canonical)", 8003)
    lines.append(f"GRIDBRIDGE_HOST_PORT_A: int = {machine_a.get('gridbridge_host_port', 8001)}")
    lines.append(f'GRIDBRIDGE_URL_DEFAULT: str = "http://localhost:{default_port}"')
    lines.append(f'GRIDBRIDGE_URL_COMPUTER_A: str = "http://localhost:{computer_a_port}"')
    lines.append("")

    # Phase C1 — Agent Contracts
    agents = schemas.get("agents", {}).get("default", {}).get("registry", {})
    if agents:
        lines.append("# ─ Agent Registry (Phase C1 SSOT) ──────────────────────────")
        lines.append(f"AGENT_REGISTRY: dict[str, dict] = {agents!r}")
        lines.append("")

    # Phase C2 — NL Intents
    intents_root = schemas.get("intents", {})
    intents = intents_root.get("default", {})
    if intents:
        lines.append("# ─ NL Intents (Phase C2 SSOT) ──────────────────────────────")
        # IntentType enum (Phase H — 하드코딩 "edgeControl" 제거 대상)
        intent_types = (intents_root.get("$defs", {})
                                    .get("IntentType", {})
                                    .get("enum", []))
        if intent_types:
            lines.append(f"INTENT_TYPES: tuple[str, ...] = {tuple(intent_types)!r}")
        lines.append(f"NL_STRATEGIES_BY_KEYWORD: dict[str, list[str]] = "
                     f"{intents.get('strategies_by_keyword', {})!r}")
        lines.append(f"NL_CONTROL_KEYWORDS: list[str] = "
                     f"{intents.get('control_keywords', [])!r}")
        lines.append(f"NL_GATE_TOKENS: list[str] = "
                     f"{intents.get('gate_tokens', [])!r}")
        lines.append(f"NL_PATTERNS: dict = {intents.get('patterns', {})!r}")
        lines.append(f"NL_CONSTRAINTS: dict = {intents.get('constraints', {})!r}")
        lines.append("")

    # Phase E — Run Modes
    modes = schemas.get("modes", {}).get("default", {}).get("modes", {})
    if modes:
        lines.append("# ─ Run Modes (Phase E SSOT) ─────────────────────────────────")
        lines.append('RUN_MODES: tuple[str, ...] = ("prod", "demo", "dev", "test")')
        lines.append(f"RUN_MODE_BEHAVIOR: dict[str, dict] = {modes!r}")
        lines.append("")

    # Phase F — Data Classification
    dataclass = schemas.get("dataclass", {}).get("default", {})
    if dataclass:
        lines.append("# ─ Data Classification (Phase F SSOT) ───────────────────────")
        lines.append(f"DATA_SOURCES: dict[str, dict] = {dataclass.get('sources', {})!r}")
        lines.append('DATA_SOURCE_LABELS: tuple[str, ...] = ("measured", "certified", "simulated", "predicted", "external", "synthetic", "mock")')
        lines.append("")

    # Phase G — Test Classification
    tests = schemas.get("tests", {}).get("default", {})
    if tests:
        lines.append("# ─ Test Classification (Phase G SSOT) ───────────────────────")
        lines.append(f"TEST_TIERS: dict[str, dict] = {tests.get('tiers', {})!r}")
        lines.append(f"TEST_GROUPS: dict[str, dict] = {tests.get('groups', {})!r}")
        lines.append(f"TEST_STAGES: dict[str, dict] = {tests.get('stages', {})!r}")
        lines.append(f"TEST_PROJECT_DEFAULT_GROUPS: dict[str, list[str]] = "
                     f"{tests.get('project_default_groups', {})!r}")
        lines.append("")

    # Phase I-1 — AI Model Registry
    models = schemas.get("models", {}).get("default", {}).get("models", {})
    if models:
        lines.append("# ─ AI Model Registry (Phase I-1 SSOT) ───────────────────────")
        lines.append(f"AI_MODELS: dict[str, dict] = {models!r}")
        lines.append("")

    # Phase I-2 — Auth Scopes
    auth = schemas.get("auth", {}).get("default", {})
    if auth:
        lines.append("# ─ Auth Scopes (Phase I-2 SSOT) ─────────────────────────────")
        lines.append(f"AUTH_SCOPES: dict[str, dict] = {auth.get('scopes', {})!r}")
        lines.append(f"AUTH_PERMISSIONS: dict[str, list[str]] = "
                     f"{auth.get('permissions', {})!r}")
        lines.append(f"AUTH_PROJECT_DEFAULT_SCOPES: dict[str, list[str]] = "
                     f"{auth.get('project_default_scopes', {})!r}")
        lines.append("")

    # Phase I-3 — Error Response
    errors = schemas.get("errors", {}).get("default", {})
    if errors:
        lines.append("# ─ Error Response (Phase I-3 SSOT) ──────────────────────────")
        lines.append(f"ERROR_CODES: dict[str, dict] = {errors.get('codes', {})!r}")
        lines.append(f"ERROR_TYPE_PREFIX: str = {errors.get('type_prefix', '')!r}")
        lines.append("")

    # Phase I-4 — MQTT Topics
    mqtt = schemas.get("mqtt", {}).get("default", {})
    if mqtt:
        lines.append("# ─ MQTT Topics (Phase I-4 SSOT) ─────────────────────────────")
        lines.append(f"MQTT_NAMESPACES: dict[str, dict] = "
                     f"{mqtt.get('namespaces', {})!r}")
        lines.append(f"MQTT_TOPIC_PATTERNS: list[dict] = {mqtt.get('topics', [])!r}")
        lines.append("")

    # Phase I-5 — Security Policy
    security = schemas.get("security", {}).get("default", {})
    if security:
        lines.append("# ─ Security Policy (Phase I-5 SSOT) ─────────────────────────")
        lines.append(f"SECURITY_HEADERS: dict[str, str] = "
                     f"{security.get('headers', {})!r}")
        lines.append(f"SECURITY_CORS: dict = {security.get('cors', {})!r}")
        lines.append(f"SECURITY_RATE_LIMITS: dict[str, str] = "
                     f"{security.get('rate_limit', {})!r}")
        lines.append("")

    # ── Phase J 신규 (7개) ──────────────────────────────────────────────────

    cmpprof = schemas.get("cmpprof", {}).get("default", {})
    if cmpprof:
        lines.append("# ─ Computer Profile (Phase J-6 SSOT) ────────────────────────")
        lines.append(f"COMPUTER_PROFILES: dict[str, dict] = "
                     f"{cmpprof.get('machines', {})!r}")
        lines.append(f"COMPUTER_SHARED_PATHS: dict[str, str] = "
                     f"{cmpprof.get('shared_ssot_paths', {})!r}")
        # Phase B-2: 머신 감지 헬퍼 (5사이트의 'H:/내 드라이브' 하드코딩 대체)
        lines.append("")
        lines.append("def detect_machine() -> str:")
        lines.append('    """SSOT COMPUTER_PROFILES.machines.*.detection 으로 현재 머신 ID 판정.')
        lines.append("")
        lines.append("    우선순위: 명시 env COMPUTER_ID > detection.method 적용 > 'B' fallback.")
        lines.append('    """')
        lines.append("    import os as _os")
        lines.append('    explicit = _os.environ.get("COMPUTER_ID", "").strip().upper()')
        lines.append("    if explicit in COMPUTER_PROFILES:")
        lines.append("        return explicit")
        lines.append("    for mid, meta in COMPUTER_PROFILES.items():")
        lines.append('        det = meta.get("detection") or {}')
        lines.append('        method = det.get("method")')
        lines.append('        if method == "path_exists":')
        lines.append('            if _os.path.exists(det.get("path", "")):')
        lines.append("                return mid")
        lines.append('        elif method == "env_var":')
        lines.append('            if _os.environ.get(det.get("env", ""), "") == det.get("value", ""):')
        lines.append("                return mid")
        lines.append('    return "B"')
        lines.append("")
        lines.append("def gridbridge_url_for_machine() -> str:")
        lines.append('    """현재 머신의 GridBridge 호스트 URL — SSOT 기반."""')
        lines.append("    mid = detect_machine()")
        lines.append("    meta = COMPUTER_PROFILES.get(mid, {})")
        lines.append('    port = meta.get("gridbridge_host_port", 8001)')
        lines.append('    return f"http://localhost:{port}"')
        lines.append("")

    usage = schemas.get("usage", {}).get("default", {}).get("usages", {})
    if usage:
        lines.append("# ─ Building Usage Map (Phase J-7 SSOT) ──────────────────────")
        lines.append(f"BUILDING_USAGES: dict[str, dict] = {usage!r}")
        lines.append("")

    i18n = schemas.get("i18n", {}).get("default", {})
    if i18n:
        lines.append("# ─ i18n Keys (Phase J-8 SSOT) ───────────────────────────────")
        lines.append(f"I18N_SUPPORTED_LANGS: tuple[str, ...] = "
                     f"{tuple(i18n.get('supported_langs', []))!r}")
        lines.append(f"I18N_FALLBACK_LANG: str = "
                     f"{i18n.get('fallback_lang', 'en')!r}")
        lines.append(f"I18N_KEYS: dict[str, dict[str, str]] = "
                     f"{i18n.get('keys', {})!r}")
        lines.append("")

    tenant_reg = schemas.get("tenant_reg", {}).get("default", {})
    if tenant_reg:
        lines.append("# ─ Tenant Regions (Phase J-9 SSOT) ──────────────────────────")
        lines.append(f"TENANT_REGIONS: dict[str, dict] = "
                     f"{tenant_reg.get('regions', {})!r}")
        lines.append(f"TENANT_TO_REGION: dict[str, str] = "
                     f"{tenant_reg.get('tenant_to_region', {})!r}")
        lines.append("")

    authpol = schemas.get("authpol", {}).get("default", {})
    if authpol:
        lines.append("# ─ Auth Policy (Phase J-10 SSOT) ────────────────────────────")
        lines.append(f"AUTH_JWT_POLICY: dict = {authpol.get('jwt', {})!r}")
        lines.append(f"AUTH_COOKIE_POLICY: dict = {authpol.get('cookie', {})!r}")
        lines.append(f"AUTH_REFRESH_POLICY: dict = "
                     f"{authpol.get('refresh_token', {})!r}")
        lines.append(f"AUTH_PROJECT_POLICY_OVERRIDES: dict = "
                     f"{authpol.get('project_overrides', {})!r}")
        lines.append("")

    pipeline = schemas.get("pipeline", {}).get("default", {})
    if pipeline:
        lines.append("# ─ Pipeline Status (Phase J-11 SSOT) ────────────────────────")
        lines.append(f"PIPELINE_DATASETS: dict[str, dict] = "
                     f"{pipeline.get('datasets', {})!r}")
        lines.append(f"PIPELINE_STAGE_ORDER: list[str] = "
                     f"{pipeline.get('stage_order', [])!r}")
        lines.append("")

    units = schemas.get("units", {}).get("default", {})
    if units:
        lines.append("# ─ Energy Units (Phase J-12 SSOT) ───────────────────────────")
        lines.append(f"ENERGY_BASE_UNITS: dict[str, str] = "
                     f"{units.get('base_units', {})!r}")
        lines.append(f"ENERGY_CONVERSIONS: dict[str, float] = "
                     f"{units.get('conversions', {})!r}")
        lines.append(f"PRIMARY_ENERGY_FACTORS: dict[str, float] = "
                     f"{units.get('primary_energy_factors', {})!r}")
        lines.append(f"EMISSION_FACTORS_KR: dict[str, float] = "
                     f"{units.get('emission_factors_kr', {})!r}")
        lines.append(f"ZEB_THRESHOLDS: dict[str, float] = "
                     f"{units.get('zeb_thresholds_kwh_m2_yr', {})!r}")
        lines.append("")

    # ── Phase K 신규 (6개) ──────────────────────────────────────────────────

    ts_shared = schemas.get("tests_shared", {}).get("default", {})
    if ts_shared:
        lines.append("# ─ Shared Test Fixtures (Phase K-13 SSOT) ───────────────────")
        lines.append(f"TESTS_SHARED: dict = {ts_shared!r}")
        lines.append("")

    logfmt = schemas.get("logfmt", {}).get("default", {})
    if logfmt:
        lines.append("# ─ Logging Format (Phase K-14 SSOT) ─────────────────────────")
        lines.append(f"LOGGING_FORMAT: dict = {logfmt!r}")
        lines.append("")

    sim_scn = schemas.get("sim_scn", {}).get("default", {})
    if sim_scn:
        lines.append("# ─ Simulation Scenarios (Phase K-15 SSOT) ───────────────────")
        lines.append(f"SIM_RUN_PERIODS: dict = {sim_scn.get('run_periods', {})!r}")
        lines.append(f"SIM_DESIGN_DAYS: dict = {sim_scn.get('design_days', {})!r}")
        lines.append(f"SIM_EMS_PATTERNS: dict = {sim_scn.get('ems_patterns', {})!r}")
        lines.append(f"SIM_PMV_THRESHOLDS: dict = "
                     f"{sim_scn.get('pmv_thresholds', {})!r}")
        lines.append(f"SIM_KO_ENVELOPE_UVALUE: dict = "
                     f"{sim_scn.get('ko_envelope_uvalue', {})!r}")
        lines.append("")

    dbmig = schemas.get("dbmig", {}).get("default", {})
    if dbmig:
        lines.append("# ─ DB Migrations (Phase K-16 SSOT) ──────────────────────────")
        lines.append(f"DB_MIGRATIONS: dict = {dbmig!r}")
        lines.append("")

    oapi_resp = schemas.get("oapi_resp", {}).get("default", {})
    if oapi_resp:
        lines.append("# ─ OpenAPI Standard Responses (Phase K-17 SSOT) ─────────────")
        lines.append(f"OPENAPI_RESPONSES: dict = "
                     f"{oapi_resp.get('standard_responses', {})!r}")
        lines.append(f"OPENAPI_AUTH_RESPONSES: list[str] = "
                     f"{oapi_resp.get('auth_required_responses', [])!r}")
        lines.append(f"OPENAPI_WRITE_RESPONSES: list[str] = "
                     f"{oapi_resp.get('write_operation_responses', [])!r}")
        lines.append(f"OPENAPI_READ_RESPONSES: list[str] = "
                     f"{oapi_resp.get('read_operation_responses', [])!r}")
        lines.append("")

    lintfmt = schemas.get("lintfmt", {}).get("default", {})
    if lintfmt:
        lines.append("# ─ Lint & Format (Phase K-18 SSOT) ──────────────────────────")
        lines.append(f"LINT_CONFIG: dict = {lintfmt!r}")
        lines.append("")

    return "\n".join(lines) + "\n"


# ── TypeScript 생성 ─────────────────────────────────────────────────────────

TS_HEADER = '''/**
 * AUTO-GENERATED constants from energy-contracts/schemas/.
 *
 * DO NOT EDIT. Run `python energy-contracts/scripts/gen_constants.py` to regenerate.
 *
 * Source SSOT: ems_strategies.json, port_allocation.json, common.json
 * Generated by: gen_constants.py (myjob/docs/SSOT_GOVERNANCE.md Phase B)
 * Source hash: {hash}
 */

export const SOURCE_HASH = "{hash}";
'''


def gen_typescript(schemas: dict) -> str:
    h = schemas_hash(schemas)
    ems = schemas["ems"]["default"]
    ports = schemas["ports"]

    lines = [TS_HEADER.format(hash=h), ""]

    codes = list(ems["strategies"].keys())
    lines.append("// ─ Strategy codes ────────────────────────────────────────────")
    lines.append(f"export const STRATEGY_CODES = {json.dumps(codes)} as const;")
    lines.append("export type StrategyCode = (typeof STRATEGY_CODES)[number];")
    lines.append(f"export const STRATEGY_PATTERN = /^M(0[0-9]|1[0-5])$/;")
    lines.append("")

    lines.append("export interface StrategyMeta {")
    lines.append("  name_en: string;")
    lines.append("  name_kr: string;")
    lines.append('  type: "single" | "combined";')
    lines.append("  components: StrategyCode[];")
    lines.append("}")
    lines.append("")
    lines.append("export const STRATEGIES: Record<StrategyCode, StrategyMeta> = {")
    for code, meta in ems["strategies"].items():
        lines.append(f"  {code}: {json.dumps(meta, ensure_ascii=False)},")
    lines.append("} as const;")
    lines.append("")

    lines.append("// ─ DR signal → strategy ─────────────────────────────────────")
    lines.append(f"export const SIGNAL_MAPPING: Record<string, StrategyCode> = "
                 f"{json.dumps(ems['signal_mapping'])};")
    lines.append("")

    lines.append("// ─ Legacy code mapping (lookup only) ────────────────────────")
    lines.append("export const LEGACY_MAPPING = "
                 + json.dumps(ems["legacy_mapping"], ensure_ascii=False) + " as const;")
    lines.append("")

    lines.append("// ─ Port allocation ──────────────────────────────────────────")
    lines.append("export const PORTS: Record<string, number> = {")
    for svc in ports.get("services", []):
        if "port" not in svc:
            continue
        key = re.sub(r"[^A-Za-z0-9]+", "_", svc["name"]).strip("_").upper()
        lines.append(f"  {key}: {svc['port']},")
    lines.append("} as const;")
    lines.append("")

    machine_a = ports.get("machines", {}).get("A", {})
    default_port = _find_service_port(ports, "GridBridge (code default)", 8001)
    computer_a_port = _find_service_port(ports, "GridBridge (Computer A canonical)", 8003)
    lines.append("// ─ Computer A override ──────────────────────────────────────")
    lines.append(f"export const GRIDBRIDGE_HOST_PORT_A = "
                 f"{machine_a.get('gridbridge_host_port', 8001)};")
    lines.append(f'export const GRIDBRIDGE_URL_DEFAULT = "http://localhost:{default_port}";')
    lines.append(f'export const GRIDBRIDGE_URL_COMPUTER_A = "http://localhost:{computer_a_port}";')
    lines.append("")

    # Phase C1
    agents = schemas.get("agents", {}).get("default", {}).get("registry", {})
    if agents:
        lines.append("// ─ Agent Registry (Phase C1) ────────────────────────────")
        lines.append(f"export const AGENT_REGISTRY = "
                     f"{json.dumps(agents, ensure_ascii=False)} as const;")
        lines.append("")

    # Phase C2
    intents_root = schemas.get("intents", {})
    intents = intents_root.get("default", {})
    if intents:
        lines.append("// ─ NL Intents (Phase C2) ────────────────────────────────")
        intent_types = (intents_root.get("$defs", {})
                                    .get("IntentType", {})
                                    .get("enum", []))
        if intent_types:
            lines.append(f"export const INTENT_TYPES = "
                         f"{json.dumps(intent_types)} as const;")
            lines.append("export type IntentType = (typeof INTENT_TYPES)[number];")
        lines.append(f"export const NL_STRATEGIES_BY_KEYWORD: Record<string, string[]> = "
                     f"{json.dumps(intents.get('strategies_by_keyword', {}), ensure_ascii=False)};")
        lines.append(f"export const NL_CONTROL_KEYWORDS = "
                     f"{json.dumps(intents.get('control_keywords', []), ensure_ascii=False)} as const;")
        lines.append(f"export const NL_GATE_TOKENS = "
                     f"{json.dumps(intents.get('gate_tokens', []), ensure_ascii=False)} as const;")
        lines.append(f"export const NL_PATTERNS = "
                     f"{json.dumps(intents.get('patterns', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const NL_CONSTRAINTS = "
                     f"{json.dumps(intents.get('constraints', {}))} as const;")
        lines.append("")

    # Phase E
    modes = schemas.get("modes", {}).get("default", {}).get("modes", {})
    if modes:
        lines.append("// ─ Run Modes (Phase E) ──────────────────────────────────")
        lines.append('export const RUN_MODES = ["prod", "demo", "dev", "test"] as const;')
        lines.append("export type RunMode = (typeof RUN_MODES)[number];")
        lines.append(f"export const RUN_MODE_BEHAVIOR = "
                     f"{json.dumps(modes, ensure_ascii=False)} as const;")
        lines.append("")

    # Phase F
    dataclass = schemas.get("dataclass", {}).get("default", {})
    if dataclass:
        lines.append("// ─ Data Classification (Phase F) ────────────────────────")
        lines.append(f"export const DATA_SOURCES = "
                     f"{json.dumps(dataclass.get('sources', {}), ensure_ascii=False)} as const;")
        lines.append('export const DATA_SOURCE_LABELS = ["measured", "certified", "simulated", "predicted", "external", "synthetic", "mock"] as const;')
        lines.append("export type DataSource = (typeof DATA_SOURCE_LABELS)[number];")
        lines.append("")

    # Phase G
    tests = schemas.get("tests", {}).get("default", {})
    if tests:
        lines.append("// ─ Test Classification (Phase G) ────────────────────────")
        lines.append(f"export const TEST_TIERS = "
                     f"{json.dumps(tests.get('tiers', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const TEST_GROUPS = "
                     f"{json.dumps(tests.get('groups', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const TEST_STAGES = "
                     f"{json.dumps(tests.get('stages', {}), ensure_ascii=False)} as const;")
        lines.append("")

    # Phase I-1 — AI Model Registry
    models = schemas.get("models", {}).get("default", {}).get("models", {})
    if models:
        lines.append("// ─ AI Model Registry (Phase I-1) ────────────────────────")
        lines.append(f"export const AI_MODELS = "
                     f"{json.dumps(models, ensure_ascii=False)} as const;")
        lines.append("")

    # Phase I-2 — Auth Scopes
    auth = schemas.get("auth", {}).get("default", {})
    if auth:
        lines.append("// ─ Auth Scopes (Phase I-2) ──────────────────────────────")
        lines.append(f"export const AUTH_SCOPES = "
                     f"{json.dumps(auth.get('scopes', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const AUTH_PERMISSIONS = "
                     f"{json.dumps(auth.get('permissions', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const AUTH_PROJECT_DEFAULT_SCOPES = "
                     f"{json.dumps(auth.get('project_default_scopes', {}), ensure_ascii=False)} as const;")
        lines.append("")

    # Phase I-3 — Error Response
    errors = schemas.get("errors", {}).get("default", {})
    if errors:
        lines.append("// ─ Error Response (Phase I-3) ───────────────────────────")
        lines.append(f"export const ERROR_CODES = "
                     f"{json.dumps(errors.get('codes', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const ERROR_TYPE_PREFIX = "
                     f"{json.dumps(errors.get('type_prefix', ''))};")
        lines.append("")

    # Phase I-4 — MQTT Topics
    mqtt = schemas.get("mqtt", {}).get("default", {})
    if mqtt:
        lines.append("// ─ MQTT Topics (Phase I-4) ──────────────────────────────")
        lines.append(f"export const MQTT_NAMESPACES = "
                     f"{json.dumps(mqtt.get('namespaces', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const MQTT_TOPIC_PATTERNS = "
                     f"{json.dumps(mqtt.get('topics', []), ensure_ascii=False)} as const;")
        lines.append("")

    # Phase I-5 — Security Policy
    security = schemas.get("security", {}).get("default", {})
    if security:
        lines.append("// ─ Security Policy (Phase I-5) ──────────────────────────")
        lines.append(f"export const SECURITY_HEADERS = "
                     f"{json.dumps(security.get('headers', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const SECURITY_CORS = "
                     f"{json.dumps(security.get('cors', {}), ensure_ascii=False)} as const;")
        lines.append(f"export const SECURITY_RATE_LIMITS = "
                     f"{json.dumps(security.get('rate_limit', {}), ensure_ascii=False)} as const;")
        lines.append("")

    # ── Phase J/K 추가 (13개) — TS는 핵심만 노출 ─────────────────────────────

    def _ts_dump(key: str, var: str, path: list[str] | None = None) -> None:
        node: dict = schemas.get(key, {}).get("default", {})
        for p in (path or []):
            node = node.get(p, {})
        if node:
            lines.append(f"export const {var} = "
                         f"{json.dumps(node, ensure_ascii=False)} as const;")

    _ts_dump("cmpprof",    "COMPUTER_PROFILES",   ["machines"])
    _ts_dump("usage",      "BUILDING_USAGES",     ["usages"])
    _ts_dump("i18n",       "I18N_KEYS",           ["keys"])
    _ts_dump("i18n",       "I18N_FALLBACK_LANG",  ["fallback_lang"])
    _ts_dump("tenant_reg", "TENANT_REGIONS",      ["regions"])
    _ts_dump("tenant_reg", "TENANT_TO_REGION",    ["tenant_to_region"])
    _ts_dump("authpol",    "AUTH_JWT_POLICY",     ["jwt"])
    _ts_dump("authpol",    "AUTH_COOKIE_POLICY",  ["cookie"])
    _ts_dump("pipeline",   "PIPELINE_DATASETS",   ["datasets"])
    _ts_dump("units",      "ENERGY_CONVERSIONS",  ["conversions"])
    _ts_dump("units",      "PRIMARY_ENERGY_FACTORS", ["primary_energy_factors"])
    _ts_dump("units",      "EMISSION_FACTORS_KR", ["emission_factors_kr"])
    _ts_dump("units",      "ZEB_THRESHOLDS",      ["zeb_thresholds_kwh_m2_yr"])
    _ts_dump("logfmt",     "LOGGING_FORMAT")
    _ts_dump("sim_scn",    "SIM_EMS_PATTERNS",    ["ems_patterns"])
    _ts_dump("oapi_resp",  "OPENAPI_RESPONSES",   ["standard_responses"])

    return "\n".join(lines)


# ── Phase M-4: dead exports 화이트리스트 필터 ─────────────────────────────

# 산출물에 항상 보존되는 심볼 (헤더/엔트리포인트)
_ALWAYS_KEEP_PY = {"SOURCE_HASH"}
_ALWAYS_KEEP_TS = {"SOURCE_HASH"}


def filter_python_output(content: str, whitelist: list[str]) -> str:
    """Python 산출물에서 화이트리스트 외 top-level 심볼(assignment+function) 제거.

    헤더(docstring/import) 및 section 주석은 보존 (cosmetic). 화이트리스트가
    빈 list 면 필터링 안 함 (전체 emit).
    """
    if not whitelist:
        return content
    keep_set = set(whitelist) | _ALWAYS_KEEP_PY
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return content
    lines = content.splitlines(keepends=True)
    keep = [True] * (len(lines) + 2)  # 1-indexed
    for node in tree.body:
        name = ""
        if isinstance(node, ast.Assign):
            if node.targets and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                name = node.target.id
        elif isinstance(node, ast.FunctionDef):
            # 함수는 항상 보존 (detect_machine, gridbridge_url_for_machine 등
            # 헬퍼는 화이트리스트 surveyor 가 못 잡는 lowercase 심볼 — 비용 대비
            # 분석 이득이 작아 일괄 keep).
            continue
        elif isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
            continue  # import/docstring 항상 유지
        else:
            continue
        if not name or name in keep_set:
            continue
        start = node.lineno
        end = node.end_lineno or start
        for ln in range(start, end + 1):
            keep[ln] = False
    new_lines = [lines[i - 1] for i in range(1, len(lines) + 1) if keep[i]]
    # 연속 빈 줄 3개 이상 → 1개로 축약 (cosmetic)
    result: list[str] = []
    blank = 0
    for line in new_lines:
        if line.strip() == "":
            blank += 1
            if blank <= 1:
                result.append(line)
        else:
            blank = 0
            result.append(line)
    return "".join(result)


# TS 한 줄 `export const NAME = ...;` 또는 다음 줄들에 걸친 `... } as const;` 케이스
_TS_EXPORT_START = re.compile(
    r"^export\s+(?:const|type|interface)\s+([A-Za-z_][A-Za-z_0-9]*)\b"
)


def filter_typescript_output(content: str, whitelist: list[str]) -> str:
    """TS 산출물에서 화이트리스트 외 export 제거.

    interface / type 은 의존 const 와 함께 keep/drop. 휴리스틱:
      - `export type X = (typeof Y)[number]` → Y 가 keep 이면 X 도 keep
      - `export interface Foo` 블록 → 항상 보존 (작아서 분석 비용 > 이득)
      - **interface 가 다른 type/const 를 참조하면 그것도 transitive 하게 keep**
        (TD-2 청산: StrategyMeta가 StrategyCode 참조 → StrategyCode + STRATEGY_CODES 모두 keep)
    """
    if not whitelist:
        return content
    keep_set = set(whitelist) | _ALWAYS_KEEP_TS
    lines = content.splitlines(keepends=True)
    n = len(lines)
    keep = [True] * (n + 1)  # 0-indexed

    # 1차 패스: top-level export 의 시작/끝/이름 식별
    blocks: list[tuple[int, int, str, str]] = []  # (start, end, name, kind)
    i = 0
    while i < n:
        line = lines[i]
        m = _TS_EXPORT_START.match(line)
        if not m:
            i += 1
            continue
        name = m.group(1)
        kind = line.lstrip().split()[1]  # const / type / interface
        # 블록 끝: 짝맞춤 까지. interface 는 `}` 단독 줄까지. 일반 `;` 종결.
        depth = 0
        j = i
        while j < n:
            for ch in lines[j]:
                if ch in "{[(":
                    depth += 1
                elif ch in "}])":
                    depth -= 1
            stripped = lines[j].rstrip()
            if depth == 0 and (stripped.endswith(";") or
                                stripped.endswith("}")):
                break
            j += 1
        blocks.append((i, j, name, kind))
        i = j + 1

    # TD-2 청산: interface 가 keep 이면 그 안에서 참조된 식별자도 keep 으로 transitive 확장.
    # interface 는 line 925-925 의 휴리스틱(always keep)으로 보존되므로 그 의존도 확장.
    # type 의 (typeof X) 도 동일 — X 가 keep set 에 들어와야 type 이 의미 있음.
    ident_re = re.compile(r"\b([A-Z][A-Za-z_0-9]*)\b")
    changed = True
    iter_guard = 0
    while changed and iter_guard < 5:
        changed = False
        iter_guard += 1
        for start, end, name, kind in blocks:
            # 이 블록이 보존 대상인지 (interface 항상, name 매칭, type+의존자 keep)
            is_kept = (
                name in keep_set
                or kind == "interface"
                or (kind == "type" and re.search(
                    r"\(typeof\s+([A-Za-z_][A-Za-z_0-9]*)\)",
                    "".join(lines[start:end + 1]),
                ) and re.search(
                    r"\(typeof\s+([A-Za-z_][A-Za-z_0-9]*)\)",
                    "".join(lines[start:end + 1]),
                ).group(1) in keep_set)
            )
            if not is_kept:
                continue
            block_text = "".join(lines[start:end + 1])
            # 블록 내 모든 식별자(PascalCase/UPPER_SNAKE) 추출 후 keep_set 확장
            for ident in ident_re.findall(block_text):
                if ident == name or ident in keep_set:
                    continue
                # 다른 블록 이름과 매칭되면 keep
                for s2, e2, n2, _k2 in blocks:
                    if n2 == ident and n2 not in keep_set:
                        keep_set.add(ident)
                        changed = True
                        break

    # 2차 패스: keep 결정
    # const/interface 는 화이트리스트 직접 매칭. type 은 의존 const 추적.
    for start, end, name, kind in blocks:
        if name in keep_set:
            continue
        if kind == "interface":
            continue  # interface 는 보존 (저비용)
        if kind == "type":
            # `export type X = (typeof Y)[number]` 패턴 추출
            block_text = "".join(lines[start:end + 1])
            dep = re.search(r"\(typeof\s+([A-Za-z_][A-Za-z_0-9]*)\)",
                            block_text)
            if dep and dep.group(1) in keep_set:
                continue
        # drop
        for k in range(start, end + 1):
            keep[k] = False
    new_lines = [lines[k] for k in range(n) if keep[k]]
    # 연속 빈 줄 축약
    result: list[str] = []
    blank = 0
    for line in new_lines:
        if line.strip() == "":
            blank += 1
            if blank <= 1:
                result.append(line)
        else:
            blank = 0
            result.append(line)
    return "".join(result)


def apply_exports_filter(content: str, lang: str, project_cfg: dict) -> str:
    """PROJECT_TARGETS[proj].exports[lang] 화이트리스트 적용."""
    exports_cfg = project_cfg.get("exports", {})
    whitelist = exports_cfg.get(lang, [])
    if not whitelist:
        return content
    if lang == "python":
        return filter_python_output(content, whitelist)
    if lang == "ts":
        return filter_typescript_output(content, whitelist)
    return content


# ── 작업 실행 ───────────────────────────────────────────────────────────────

def write_target(content: str, out_path: Path) -> bool:
    """파일이 이미 동일하면 False (변경 없음), 다르면 True."""
    if out_path.exists():
        old = out_path.read_text(encoding="utf-8")
        if old == content:
            return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return True


def regenerate_all(check_only: bool = False) -> int:
    schemas = load_schemas()
    drift = 0
    for proj, project_cfg in PROJECT_TARGETS.items():
        for lang in ("python", "ts"):
            rel_path = project_cfg.get(lang)
            if not rel_path:
                continue
            out = WORKSPACE_ROOT / rel_path
            full = gen_python(schemas) if lang == "python" else gen_typescript(schemas)
            content = apply_exports_filter(full, lang, project_cfg)
            if check_only:
                if not out.exists():
                    print(f"[gen_constants] MISSING: {rel_path}")
                    drift += 1
                elif out.read_text(encoding="utf-8") != content:
                    print(f"[gen_constants] DRIFT: {rel_path}")
                    drift += 1
                else:
                    print(f"[gen_constants] OK:    {rel_path}")
            else:
                changed = write_target(content, out)
                tag = "WROTE" if changed else "SAME "
                print(f"[gen_constants] {tag} {rel_path}")
    if check_only:
        print(f"\n[gen_constants] drift {drift} files")
        return 1 if drift else 0
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["python", "ts"],
                    help="단일 생성 시 언어 지정")
    ap.add_argument("--out", help="단일 생성 시 출력 경로")
    ap.add_argument("--check", action="store_true",
                    help="등록된 모든 타겟의 drift 검사 (CI용)")
    ap.add_argument("--all", action="store_true",
                    help="등록된 모든 타겟 재생성")
    args = ap.parse_args()

    if args.check:
        return regenerate_all(check_only=True)
    if args.all:
        return regenerate_all(check_only=False)

    if not args.target or not args.out:
        ap.print_help()
        print("\n[gen_constants] --all 또는 --check 권장. 단일 모드는 --target + --out 필수.")
        return 2

    schemas = load_schemas()
    content = gen_python(schemas) if args.target == "python" else gen_typescript(schemas)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = WORKSPACE_ROOT / out_path
    changed = write_target(content, out_path)
    print(f"[gen_constants] {'WROTE' if changed else 'SAME '} {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
