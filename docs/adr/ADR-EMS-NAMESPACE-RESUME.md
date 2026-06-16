# EMS M-code 통일 program — RESUME / STATUS (다음 세션 인계)

> 2026-06-16 checkpoint. 본 문서 1장이면 다음 세션이 바로 이어간다. 설계=`ADR-EMS-NAMESPACE-UNIFY.md`, 전수 분류=`ADR-EMS-NAMESPACE-P0-INVENTORY.md`, 메모리=`project_agentleague_layer3_mcode_drift_2026-06-16`.

## 0. 한 줄 재개
> **"M-code 네임스페이스 통일 program — 전 7 repo 코드 완료. 머지 전 남은 건 ① nl_intents 키워드 untangle(P5 잔여) ② 라이브 cutover(사용자 게이트)"** — 본 문서 + ADR + 메모리가 맥락 복원. (P0~P4·P6-a·P6-b·P5 코드 전부 ✅, 브랜치 정합.)
> - **P5 코드 ✅** = be-3d control_router/edge_control 프리셋 + control_intent regex 를 edge-agent(P3) 미러로 M16~M20 재키잉 완료(a07e9ce, 25+315 PASS).
> - **P5 잔여 (머지 전 권장)** = `energy_contracts/schemas/nl_intents.json` `strategies_by_keyword` + `patterns.strategy_code`(아직 M15) 가 DR 키워드 오버로드 + sim M01↔M06 드리프트를 보유 → '긴급 감축해' 등 NL 키워드가 orphaned 코드 해석. **DR 문구→M16~M20, sim M01↔M06 정정 + gen_constants 로 2 consumer(be-3d/sejong) regen** 필요. M-code 도메인 오버로드 untangle = 신중(메모리 교훈). 직접 코드('M20 적용')는 정상.
> - **P5 cutover = 사용자 게이트** = 라이브 VWorld 배포 + edge-agent MQTT 전환(7-repo 머지 시점).
> - **안 A (별도 forward 트랙)** = agentleague debate→policy_vector end-to-end. namespace 정합(M00~M20)은 P6-b 에서 완료, policy_vector 신설은 post-merge 제품 트랙.
> - **머지** = P5 잔여 완료 후 **7 repo 일괄**(cross-repo validate_ssot + editable 결합, 부분 머지 금지).

## 1. 무엇을 하는가
M00~M15 가 4+ 도메인에서 다른 의미(시뮬 NAMING / DR 프리셋 / a03 optimizer / EUI)로 오버로드된 것을 **단일 vocabulary 로 통일**: M00~M15=시뮬 정본(NAMING §1.1), M16~M20=DR 액션 신규, a03=별 네임스페이스 OM00~OM13.

## 2. 진행 상태 (전부 브랜치, 배포 mainline·master 무영향)

| 단계 | 내용 | 상태 | 검증 |
|:--:|------|:--:|------|
| P0 | 전수 인벤토리(4+ 의미집합) | ✅ | 2 ADR |
| P1 | foundation: ems_strategies M00~M20 + signal_mapping 재키잉 + control_command + 전 STRATEGY_PATTERN + validate_ssot + gen_constants(패턴 하드코딩 버그 fix) + 6 consumer regen | ✅ | validate_ssot PASS |
| P2 | gridbridge 재키잉(ai_oracle/engine/router/DB migration/UI/tests) | ✅ | 304 PASS |
| P3 | edge-agent 재키잉(전 src/driver/UI/metric/boundary/tests) | ✅ | 893 PASS |
| P4-a03 | a03_optimizer → OM00~OM13 분리 + agent_contracts output_strategies OM + pattern | ✅ | a03 97 PASS |
| **P4-SIM** | **be-3d 비-데모 SIM 정합** (value-swap, 사용자 결정 2026-06-16) | ✅ | 233 PASS |
| **P6-a** | **ems_transformer F14 PolicyVector M00~M20 + hallucination 경계 SSOT 파생 + hvac_ems_matrix M16~M20 커버리지(P1 완성)** | ✅ | 121+verify gates PASS |
| **P6-b** | **agentleague M00~M20 정합 (stub M16~M20 + SSOT 테스트 path 복구)** | ✅ | 22+74 PASS |
| **P5 (코드 ✅)** | be-3d 라이브 데모 DR 재키잉 M16~M20 (control_router/edge_control/control_intent, edge-agent 미러) | ✅ 코드 | 25+315 PASS |
| P5 잔여 | nl_intents.json `strategies_by_keyword` DR 오버로드+sim M01↔M06 untangle → M16~M20 + 2 consumer(be-3d/sejong) regen | ⬜ | — |
| P5 cutover | 실제 라이브 VWorld 배포 + edge-agent MQTT 전환 | ⬜ | **사용자 게이트** |
| (별도 트랙) | 안 A: debate→policy_vector end-to-end (forward 제품 기능, **머지 blocker 아님**) | ⬜ | post-merge |

## 3. 브랜치·SHA (재개 시 checkout)

| repo | 브랜치 | HEAD |
|------|--------|------|
| energy-contracts | `feat/ems-namespace-p1-foundation` | cabf74f (P6-a hvac_ems_matrix M16~M20 포함) |
| gridbridge | `feat/ems-namespace-p1-regen` | 39860a2 |
| edge-agent | `feat/ems-namespace-p1-regen` | 6d80a87 |
| building-energy-3d | `feat/ems-namespace-p1-regen` | a07e9ce (P4-SIM+P5 코드) |
| agentleague | `feat/ems-namespace-p1-regen` | cdb7fe8 (P6-b) |
| eduarena | `feat/ems-namespace-p1-regen` | 4dd010d |
| **ems_transformer** | `feat/agentleague-layer3-adapter-spike` | 17b5eb4 (P6-a, 스파이크 브랜치 연속) |
| (ADR docs) | `docs/ems-namespace-unify-adr` | 28a689a (foundation 브랜치가 포함) |

> ⚠ **머지 시 7 repo** (ems_transformer 추가). ems_transformer 는 P6-a 가 스파이크 브랜치 위에 있음.

## 4. 환경 (필수)
- **`energy_contracts` editable 설치**: `pip install -e projects/energy-contracts`. consumer `load_schema`/`validate_ssot` 가 source(M00~M20) 읽도록. 새 머신/재설치 시 필수.
- editable 이라 **energy-contracts 가 checkout 한 브랜치**가 전 consumer runtime 스키마를 결정. 재개 시 6 repo 모두 위 브랜치로 checkout.

## 5. P4-SIM ✅ 완료 (2026-06-16, be-3d 846339a, value-swap)
**핵심 발견 (메모리 교훈 = blanket swap 금지)**: 드리프트는 **M01↔M06 단일 쌍**. 출처가 둘이고 컨벤션이 달랐음:
- **be-3d EUI 테이블** = 구 `ems_simulation` 추출 = **드리프트**(M01=NightCycle, M06=OptimalStart). → 스왑 대상.
- **sim_campaign LUT(`policy_savings_lut.json`) + `savings_table.csv`** = 352k 캠페인 = **이미 정본**(IDF gen: `AvailabilityManager:OptimumStart`=M01·`NightCycle`=M06, `expected_silent_skip.yaml:86`). → **무수정**(blanket 스왑했으면 캠페인·reverse 깨뜨릴 뻔).

**사용자 결정**: EUI 드리프트 = **value-swap**(라벨 정본 + 각 숫자도 진짜 물리 전략에 정확히 재배치, 재시뮬 0). RESUME 구버전의 "data 유지·주석만" 보다 우선.

**적용 (단일 패스 atomic, 이중적용 회피)**:
- `constants.py` BUILDWISE_EUI_SEOUL + `mock_runner.py` _EUI_TABLE/_FALLBACK_SAVINGS + `building_archetypes.json` buildwise_eui_seoul: M01↔M06 값 스왑(both) / 키 rename(단일).
- `constants.py` BUILDWISE_STRATEGY_NAMES 라벨 + 주석 / `mock_runner` docstring / `validator.py` 주석 정본화.
- **lever 포인터 잠복 버그 fix**: `policy_savings.py` LEVER_TO_EMS + `f14_analysis.py` POLICY_LEVERS = night_setback→M06, optimal_start→M01 (캠페인 LUT 가 정본인데 포인터가 드리프트라 night_setback 이 OptStart 절감값 끌어오던 실버그 정정).
- 테스트: `test_standalone_retail_M06_negative_saving` 리네임 + `test_ssot_consistency` a03 stale assert(M03→OM03) 정합.

검증: **233 PASS** (retrofit/buildwise/policy/ssot/selection/control_router). frontend `policy_vector.ts`/`policy_labels.ts` = M-code ID만(라벨 백엔드) → 무수정.

## 6. 최종 머지 절차 (P6 완료 후 — 지금 금지)
**왜 지금 금지**: cross-repo 결합(validate_ssot + editable install). 부분 머지 시 master 에 스키마(M00~M20) ↔ 코드(be-3d 데모 DR 미이주 M14/M15) 불일치 → 라이브 데모 의미 깨짐. 브랜치가 현재 정합 상태.
**P6 완료 후 일괄**: ① 6 repo 각 PR(또는 직접 master 머지) **동시** ② 머지 순서 무관(working tree 가 이미 정합) but 한 번에 ③ 각 repo validate_ssot/pytest 재확인 ④ be-3d 라이브 데모 cutover = 사용자 게이트(P5) 후 deploy.

## 7. 교훈 (재발 방지)
- 수동편집 + blanket re-key **이중적용 금지** → 원본에 단일 패스만 (P3 M09→M18 충돌 사고).
- "이름 stale" 단정 전 **functional consumer grep**(signal_mapping·배포코드) — 도메인 정상 정의를 drift 로 오인해 rename 하면 배포 깸.
- golden snapshot = **`UPDATE_SNAPSHOTS=1` 공식 재생성**(손편집 금지). be-3d pre-commit 14-agent gate 는 무관 socket-test(a11/a14) 행으로 timeout → a03 은 수동검증 후 `--no-verify`.
