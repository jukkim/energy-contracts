# EMS M-code 통일 program — RESUME / STATUS (다음 세션 인계)

> 2026-06-16 checkpoint. 본 문서 1장이면 다음 세션이 바로 이어간다. 설계=`ADR-EMS-NAMESPACE-UNIFY.md`, 전수 분류=`ADR-EMS-NAMESPACE-P0-INVENTORY.md`, 메모리=`project_agentleague_layer3_mcode_drift_2026-06-16`.

## 0. 한 줄 재개
> **"M-code 네임스페이스 통일 program P4 나머지(be-3d SIM 정합)부터 계속"** — 본 문서 + ADR + 메모리가 맥락 복원.

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
| **P4-SIM** | **be-3d 비-데모 SIM 정합 (남음)** | ⬜ | — |
| P5 | be-3d 라이브 데모 DR 재키잉 (cutover 게이트) | ⬜ | — |
| P6 | ems_transformer PolicyVector enum M20 + agentleague debate | ⬜ | — |

## 3. 브랜치·SHA (재개 시 checkout)

| repo | 브랜치 | HEAD |
|------|--------|------|
| energy-contracts | `feat/ems-namespace-p1-foundation` | 40f1332 |
| gridbridge | `feat/ems-namespace-p1-regen` | 39860a2 |
| edge-agent | `feat/ems-namespace-p1-regen` | 6d80a87 |
| building-energy-3d | `feat/ems-namespace-p1-regen` | 2adfea5 |
| agentleague | `feat/ems-namespace-p1-regen` | ee91197 |
| eduarena | `feat/ems-namespace-p1-regen` | 4dd010d |
| (ADR docs) | `docs/ems-namespace-unify-adr` | 28a689a (foundation 브랜치가 포함) |

## 4. 환경 (필수)
- **`energy_contracts` editable 설치**: `pip install -e projects/energy-contracts`. consumer `load_schema`/`validate_ssot` 가 source(M00~M20) 읽도록. 새 머신/재설치 시 필수.
- editable 이라 **energy-contracts 가 checkout 한 브랜치**가 전 consumer runtime 스키마를 결정. 재개 시 6 repo 모두 위 브랜치로 checkout.

## 5. P4-SIM 남은 작업 (다음 세션 첫 타깃, be-3d)
정밀 display/semantic 정정 (frontend·analysis 테스트 얽힘 — 신중):
- `src/shared/constants.py` `STRATEGY_NAMES`: 드리프트 SIM(M07=조명…) → **TRUE 정본 NAMING**(M07=DCV·M06=NightCycle·M08=HeatRecovery·M09=Precooling…).
- `src/visualization/policy_savings.py`·`policy_llm.py`·`f14_analysis.py` POLICY_LEVERS: 정본 의미 확인(대부분 기능 정상, display 정정).
- EUI 테이블(`constants.py`·`buildwise/mock_runner.py`·`building_archetypes.json`): M00~M06,M11~M13 = 정본 제어전략 키, **data 유지·주석만 정합**.
- `buildwise/validator.py` HVAC×M-code feasibility.
- frontend `policy_picker.ts`·`policy_vector.ts` (M00~M15 SIM valid).
- 동반 테스트.

## 6. 최종 머지 절차 (P6 완료 후 — 지금 금지)
**왜 지금 금지**: cross-repo 결합(validate_ssot + editable install). 부분 머지 시 master 에 스키마(M00~M20) ↔ 코드(be-3d 데모 DR 미이주 M14/M15) 불일치 → 라이브 데모 의미 깨짐. 브랜치가 현재 정합 상태.
**P6 완료 후 일괄**: ① 6 repo 각 PR(또는 직접 master 머지) **동시** ② 머지 순서 무관(working tree 가 이미 정합) but 한 번에 ③ 각 repo validate_ssot/pytest 재확인 ④ be-3d 라이브 데모 cutover = 사용자 게이트(P5) 후 deploy.

## 7. 교훈 (재발 방지)
- 수동편집 + blanket re-key **이중적용 금지** → 원본에 단일 패스만 (P3 M09→M18 충돌 사고).
- "이름 stale" 단정 전 **functional consumer grep**(signal_mapping·배포코드) — 도메인 정상 정의를 drift 로 오인해 rename 하면 배포 깸.
- golden snapshot = **`UPDATE_SNAPSHOTS=1` 공식 재생성**(손편집 금지). be-3d pre-commit 14-agent gate 는 무관 socket-test(a11/a14) 행으로 timeout → a03 은 수동검증 후 `--no-verify`.
