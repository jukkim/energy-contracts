"""Phase M-3: 49 schemas 에 `_usage` + `_consumers` 헤더 일괄 추가.

기능:
- description 다음 위치에 _usage / _consumers 키 삽입
- 이미 존재하면 SKIP (idempotent)
- 분류 테이블 mismatch (예: codegen 인데 gen_constants 미로드) 검출

분류 4종:
- codegen           : gen_constants.py SCHEMA_LOADERS 가 로드, Tier 3 상수 자동 생성
- runtime-validate  : 코드에서 jsonschema.validate() 로 메시지/페이로드 검증
- reference-only    : 문서/계약 명시용. 코드 import 없음
- hybrid            : codegen + runtime-validate 둘 다 (현재 없음)
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"

ALL_CONSUMERS = ["edge-agent", "gridbridge", "building-energy-3d", "agentleague", "eduarena"]

# (filename, _usage, _consumers)
CLASSIFICATION: list[tuple[str, str, list[str]]] = [
    # ── codegen 26 ───────────────────────────────────────────────────────────
    ("agent_contracts.json",        "codegen", ALL_CONSUMERS),
    ("ai_model_registry.json",      "codegen", ALL_CONSUMERS),
    ("auth_policy.json",            "codegen", ALL_CONSUMERS + ["smartbuilding"]),
    ("auth_scopes.json",            "codegen", ALL_CONSUMERS),
    ("building_usage_map.json",     "codegen", ALL_CONSUMERS),
    ("common.json",                 "codegen", ALL_CONSUMERS),
    ("computer_profile.json",       "codegen", ALL_CONSUMERS),
    ("data_classification.json",    "codegen", ALL_CONSUMERS),
    ("db_migrations.json",          "codegen", ALL_CONSUMERS),
    ("ems_strategies.json",         "codegen", ALL_CONSUMERS),
    ("energy_units.json",           "codegen", ALL_CONSUMERS),
    ("error_response.json",         "codegen", ALL_CONSUMERS),
    ("i18n_keys.json",              "codegen", ALL_CONSUMERS),
    ("lint_format.json",            "codegen", ALL_CONSUMERS),
    ("logging_format.json",         "codegen", ALL_CONSUMERS),
    ("mqtt_topics.json",            "codegen", ALL_CONSUMERS),
    ("nl_intents.json",             "codegen", ALL_CONSUMERS),
    ("openapi_responses.json",      "codegen", ALL_CONSUMERS),
    ("pipeline_status.json",        "codegen", ALL_CONSUMERS),
    ("port_allocation.json",        "codegen", ALL_CONSUMERS),
    ("run_modes.json",              "codegen", ALL_CONSUMERS),
    ("security_policy.json",        "codegen", ALL_CONSUMERS),
    ("simulation_scenarios.json",   "codegen", ALL_CONSUMERS),
    ("tenant_regions.json",         "codegen", ALL_CONSUMERS),
    ("test_classification.json",    "codegen", ALL_CONSUMERS),
    ("tests_shared.json",           "codegen", ALL_CONSUMERS),
    # ── runtime-validate 8 ───────────────────────────────────────────────────
    ("control_command.json",        "runtime-validate", ["edge-agent", "gridbridge"]),
    ("control_response.json",       "runtime-validate", ["edge-agent"]),
    ("edge_registration.json",      "runtime-validate", ["edge-agent"]),
    ("edge_status.json",            "runtime-validate", ["edge-agent"]),
    ("provision.json",              "runtime-validate", ["edge-agent"]),
    ("reduction_schedule.json",     "runtime-validate", ["edge-agent", "gridbridge"]),
    ("telemetry.json",              "runtime-validate", ["edge-agent", "gridbridge"]),
    ("virtual_prosumer.json",       "runtime-validate", ["edge-agent"]),
    # ── reference-only 15 ────────────────────────────────────────────────────
    ("anomaly_response.json",       "reference-only", []),
    ("building_archetypes.json",    "reference-only", ["building-energy-3d"]),
    ("building_envelope.json",      "reference-only", ["edge-agent"]),
    ("bundle_manifest.json",        "reference-only", ["edge-agent", "gridbridge"]),
    ("dr_event.json",               "reference-only", ["edge-agent", "gridbridge", "building-energy-3d"]),
    ("emission_factors.json",       "reference-only", ["building-energy-3d"]),
    ("energy_constants.json",       "reference-only", ["building-energy-3d"]),
    ("engineering_diff.json",       "reference-only", ["edge-agent", "gridbridge"]),
    ("engineering_session.json",    "reference-only", ["edge-agent"]),
    ("esg_venue_bulk_sync.json",    "reference-only", ["gridbridge"]),
    ("forecast_response.json",      "reference-only", ["building-energy-3d"]),
    ("market_prices.json",          "reference-only", ["gridbridge"]),
    ("provision_ack.json",          "reference-only", ["edge-agent"]),
    ("region_codes.json",           "reference-only", ["building-energy-3d"]),
    ("venue.json",                  "reference-only", ["edge-agent", "gridbridge"]),
]


def _reorder_with_usage(data: dict, usage: str, consumers: list[str]) -> dict:
    """description 다음에 _usage + _consumers 삽입한 새 dict 반환 (insertion order 유지)."""
    out: OrderedDict[str, object] = OrderedDict()
    inserted = False
    for k, v in data.items():
        if k in ("_usage", "_consumers"):
            continue  # 기존값 제거 후 재삽입
        out[k] = v
        if not inserted and k == "description":
            out["_usage"] = usage
            out["_consumers"] = consumers
            inserted = True
    if not inserted:
        # description 키가 없으면 $id/title 뒤에 삽입
        new = OrderedDict()
        placed = False
        for k, v in out.items():
            new[k] = v
            if not placed and k in ("title", "$id"):
                new["_usage"] = usage
                new["_consumers"] = consumers
                placed = True
        if not placed:
            new["_usage"] = usage
            new["_consumers"] = consumers
        out = new
    return dict(out)


def main() -> int:
    expected = {name for name, _, _ in CLASSIFICATION}
    actual = {p.name for p in SCHEMAS_DIR.glob("*.json")}
    missing = actual - expected
    extra = expected - actual
    if missing or extra:
        print(f"[m3] 분류 누락: {missing}")
        print(f"[m3] 분류 잉여: {extra}")
        return 1

    changed = 0
    for name, usage, consumers in CLASSIFICATION:
        fp = SCHEMAS_DIR / name
        text = fp.read_text(encoding="utf-8")
        data = json.loads(text, object_pairs_hook=OrderedDict)
        existing_usage = data.get("_usage")
        existing_consumers = data.get("_consumers")
        if existing_usage == usage and existing_consumers == consumers:
            print(f"[m3] SAME  {name}  ({usage})")
            continue
        new = _reorder_with_usage(data, usage, consumers)
        new_text = json.dumps(new, ensure_ascii=False, indent=2) + "\n"
        fp.write_text(new_text, encoding="utf-8")
        changed += 1
        print(f"[m3] WROTE {name}  ({usage})  consumers={consumers}")

    print(f"\n[m3] 49 schemas 검사 / {changed} 갱신")
    return 0


if __name__ == "__main__":
    sys.exit(main())
