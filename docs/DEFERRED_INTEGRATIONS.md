# Deferred Integrations — energy-contracts

> 사냥꾼 라운드(2026-06-08) 산출. 본 repo 단독으로 완결할 수 없고 **cross-folder/consumer 조율**이
> 필요한 항목을 기록한다. 각 항목은 fix 명세가 확정돼 있으며, coordinated SSOT bump 시 일괄 처리한다.

## 배경 — 왜 deferred 인가

energy-contracts 는 Tier 2 SSOT 허브다. `gen_constants.py` 가 로드하는 schema 의 내용/메타데이터가
바뀌면 `schemas_hash` 가 변해, 5~6 consumer repo(edge-agent / gridbridge / building-energy-3d ×2 /
agentleague / eduarena)의 `_generated_constants.{py,ts}` 를 **모두 regen** 해야 한다(각 repo 의
ssot-drift CI 게이트가 강제). 따라서 hash 를 바꾸는 schema 변경은 단일 bug-fix PR 이 아니라
**coordinated consumer bump** 으로 처리한다.

---

## D-1 (사냥꾼 M4) — esg_policy / dr_dispatch_event `_usage` 오분류

| 항목 | 내용 |
|------|------|
| 파일 | `energy_contracts/schemas/esg_policy.json`, `dr_dispatch_event.json` |
| 현상 | 두 schema 는 `gen_constants.py` 가 DR_TYPES/MANAGEMENT_MODES/BID_STRATEGIES/DISTRIBUTION_ALGORITHMS/DISPATCH_SOURCES/DISPATCH_STATUSES 상수로 codegen 하는 **codegen 입력**인데 `_usage="runtime-validate"` 로 선언됨. `validate_ssot.check_schema_usage_headers` 의 단방향 검사로는 미탐지. |
| Fix | 두 schema `_usage` → `"hybrid"`. + `validate_ssot` 에 역방향 가드 `check_codegen_input_usage()` 신설(gen 이 로드하는 schema 는 `_usage ∈ {codegen, hybrid}` 강제). 감사 결과 그 가드는 이 2건 외 false-positive 0. |
| Cascade | `_usage` 는 hash 입력 → 6 consumer regen + commit 필요. |
| 상태 | ✅ **RESOLVED 2026-06-08** (v0.3.5 coordinated bump). 두 schema `_usage`→`hybrid`, `check_codegen_input_usage()` 가드 신설, 6 consumer regen(hash `f462482943b38ce1`→`05d50c0601204d89`). |

## D-2 (사냥꾼 M7) — ems_strategies `legacy_mapping.gcs_e_codes` ↔ legacy_ems_code_mapping 모순

| 항목 | 내용 |
|------|------|
| 파일 | `energy_contracts/schemas/ems_strategies.json` (`default.legacy_mapping.gcs_e_codes`) |
| 현상 | E1/E2/E7/E10/E11 이 `legacy_ems_code_mapping.json`(전용 drift-guard SSOT, drift_note 근거 보유)와 다른 M-code 로 매핑(E1↔E2 정확히 flip 등). `ems_strategies` 쪽이 provenance 없는 stale 중복. |
| 정본 | `legacy_ems_code_mapping.json` 의 `deprecated_e_codes` (E1→M06, E2→M01, E7→M04, E10→M11, E11→M12). |
| Fix | `ems_strategies.json#default.legacy_mapping.gcs_e_codes` 5건을 정본값으로 정정. + `validate_ssot` 에 `check_legacy_code_consistency()` 신설(두 파일 maps_to 교차 비교). |
| Cascade | `ems_strategies.json` 은 gen 로드 + `LEGACY_MAPPING` 상수로 codegen → 6 consumer regen + commit 필요. |
| 상태 | ✅ **RESOLVED 2026-06-08** (v0.3.5 coordinated bump). E1→M06/E2→M01/E7→M04/E10→M11/E11→M12 정정, `check_legacy_code_consistency()` 가드 신설, 6 consumer `LEGACY_MAPPING` regen. 참고: 자매 건 **S2**(legacy_ems_code_mapping 내부 모순)는 hash 무관이라 이전 PR 에서 정정(M09→M08). |

## D-3 (사냥꾼 LOW) — CLAUDE.md "20 CORE_KEYWORDS" 로컬 검증 불가

| 항목 | 내용 |
|------|------|
| 파일 | `CLAUDE.md` SR-2 mirror 헤더 (line ~15) |
| 현상 | "20 CORE_KEYWORDS (v1.9.2 16 + SR-2 4)" 라고 선언하나, 어떤 토큰이 keyword 인지 enumeration 이 본 repo 에 없음. authoritative 리스트와 verifier(`verify_cross_folder_mirror_drift.py`)는 sibling **ai-champion-2026** 에만 존재 → 본 repo 단독으로 "정확히 20개"를 검증 불가. |
| Fix | ai-champion-2026 의 verifier 와 lock-step 으로, CLAUDE.md 하단(또는 docs)에 20 CORE_KEYWORDS 명시 리스트를 박아 로컬 검증 가능하게. **단 enumeration SSOT 가 sibling 이라 cross-folder 조율 필요** — 단독 추가 시 mirror gate 와 불일치 위험. |
| 상태 | ✅ **RESOLVED 2026-06-08** (v0.3.6). CLAUDE.md `MIRROR_CORE_KEYWORDS_BASE_V1` enumeration 블록(20 토큰 명시) + 로컬 가드 `check_mirror_core_keywords()` + ai-champion-2026 verifier lock-step(`check_energy_contracts_enumeration()`, enumeration↔BASE_KEYWORDS 동기). 본 repo 단독 로컬 검증 가능해짐. |

---

## 처리 절차 (coordinated bump 시)

1. D-1/D-2 schema 정정 + 대응 `validate_ssot` 가드 신설
2. `python scripts/validate_ssot.py --check all` → `python scripts/gen_constants.py --all`
3. 6 consumer repo `_generated_constants.{py,ts}` regen → 각 repo 별 commit/PR
4. 각 consumer `pytest tests/test_ssot_consistency.py` PASS 확인
5. D-3 은 ai-champion-2026 `verify_cross_folder_mirror_drift.py` 갱신과 동시 진행
