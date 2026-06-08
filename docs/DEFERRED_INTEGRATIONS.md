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

---

## W-1 (Tier 1 wheel schema) — `drift_report` / `retrain_request` 신설 — ⏸ TRIGGER 미충족 (보류)

> 위 D-1/D-2/D-3 와 성격이 다름: 사냥꾼 fix 가 아니라 **트리거 대기 forward-looking 통합**.
> arch A5/A11 3-tier 분류상 Tier 1(wheel) 후보 2건. 상세 메모리 `[[project_tier1_wheel_pending]]`.

| 항목 | 내용 |
|------|------|
| 산출물 | `schemas/drift_report.json` (DriftMonitor 결과: series별 PSI/KS/baseline_n/current_n/suppressed), `schemas/retrain_request.json` (RetrainOrchestrator dispatch: model_id/trigger_type t1·t2·t3/reason{psi,ks}/mode) |
| 후속 | `gen_constants.py --all` enum 추가(6 consumer regen) → wheel build → **3 repo(ingestion-worker+be-3d+smartbuilding) pyproject pin atomic 갱신** |
| 명세 SSOT | ingestion-worker `src/ingestion/services/retrain_orchestrator.py` 의 `DriftScore`/`TriggerDecision` dataclass + 마이그 009 `retrain_jobs`. **임의 작성 금지** — 명세는 ingestion-worker 측에서 확정 |

### TRIGGER 정의 + 2026-06-09 재검증 (미충족 확정)

wheel 진입 조건 = **2개 이상 sibling 이 wheel 계약으로 read/receive** (arch A11/A5). 2026-06-09 코드 교차검증 결과 **미충족**:
- ingestion-worker `RetrainOrchestrator` 는 **queue 패턴(arch A8)** — `MLTrigger._insert_retrain_job` 가 `retrain_jobs` **DB INSERT 만** 수행, JSON Schema 계약 emit/receive 안 함 (docstring 명시 "sibling consumer 별도 PR 후 완전 가동")
- sibling wheel read **0건**: be-3d `src/` 에 `drift_report`/`retrain_request` wheel read 없음. smartbuilding 은 `from energy_contracts` import 없이 `retrain_jobs` **DB 폴링**으로 소비(`smartbuilding/api/{config,routers/retrain}.py`, 마이그 009 + W7-ext)
- → 지금 작성 시 소비자 0건 wheel 진입 = 룰 위반 + 불필요 3-repo pin bump. **보류.**
- 실제 trigger = RetrainOrchestrator 가 queue→**wheel 계약 emit** 으로 전환되어 sibling 이 wheel read/receive 진입할 때 (= ingestion-worker 아키텍처 변경, 별도 세션)

### ⚠️ 토글-친화성 관점 — wheel schema 는 "쉬운 전환"에 무관 (2026-06-09 분석)

사용자 의도("에이전트 가동 ↔ 직접 수집 을 나중에 쉽게 전환")에서 본 결론:
- **전환 토글 본체** = campaign `ADR-003 OWNERSHIP (be_3d_direct ↔ ingestion_worker)` 플래그 + collector standby 보존. **이미 가벼움**(docs 6 + ADR 1, 코드 0, 마이그 0). 이게 "쉬운 전환"을 이미 충족
- wheel schema(W-1)는 **수집 축이 아니라 ML 오케스트레이션 emit 축** → 토글을 더 쉽게 만들지 **않음**
- 오히려 지금 만들면 3-repo pin 을 **조기 동결** → 실제 배선 시 모양 바뀌면 또 6-repo regen → 토글이 **무거워짐**(standby 의 "코드는 살리되 계약 비동결" 철학에 역행)
- 토글 양방향을 매끄럽게 하려면 손댈 곳 = **be-3d 수신 경로(W13 cutover, 현재 gold 소비 0건)** 이지 본 repo wheel schema 아님
- **결론**: "쉬운 전환" 목적이라면 W-1 은 **보류가 정답** (건드릴수록 손해)
