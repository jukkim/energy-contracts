# ADR — EMS M-code 단일 vocabulary 통일 + DR 액션 정당 확장 (M16~M20)

> Status: **Design Accepted, 실행 PAUSED (2026-06-16) — 실행 중 scope 대폭 확장 발견(§8)으로 사용자 재결정 대기.** Owner: energy-contracts (SSOT) · Driver: agentleague→Layer3 통합 사냥꾼 검토에서 발견.
> **실행 이력**: foundation(S1~S5) 1회 구현 + validate_ssot PASS 검증까지 도달했으나, consumer code 재키잉 중 §8 의 3차 의미·deployed 경로·테스트·라이브 데모 광범위 침투 발견 → **전 변경 revert(clean), 본 ADR(설계)만 보존**. 재개는 §9 staged program 으로.
> Cross-link: `8.simulation/ems_transformer/docs/DEBATE_LAYER3_INTEGRATION_HANDOFF.md` §10.5/§10.6 · `8.simulation/docs/NAMING_UNIFICATION.md` §1.1.

## 1. 문제

M00~M15 가 **두 도메인이 서로 다른 의미로 사용**(13/16 충돌):
- **시뮬 카탈로그** (NAMING §1.1) — ems_transformer·sim_campaign·KBEP·reverse. EnergyPlus 제어 알고리즘. 예: M07=DCV.
- **DR/grid 카탈로그** — energy-contracts `default.strategies`+`signal_mapping`, edge-agent `strategies.py`(배포), gridbridge `ai_oracle.py`, be-3d `edge_control.py`(라이브 VWorld 데모). 제어 프리셋. 예: M07=조명제어.

그러나 `control_command.json` strategy enum = M00~M15 단일 계약이고 모든 모듈이 "통일코드 M00~M15, SSOT ems_strategies.json"를 표방 → **설계 의도 = 단일 vocabulary**. 즉 충돌은 DR 측이 일부 코드에 정본(NAMING)과 다른 프리셋을 오배정한 것.

## 2. 결정

**단일 vocabulary 로 통일하고, 시뮬에 없는 DR 액션만 정본 신규 코드로 확장.**
1. **M00~M15 = NAMING §1.1 정본 의미** 로 전 생태계 고정. 시뮬 데이터·학습모델 무변경(이미 정본 사용).
2. DR 프리셋 중 정본과 같은 액션은 정본 코드 재사용, 다른 정본 액션이면 재지정, **시뮬에 없는 액션만 신규 M16~M20**.
3. `#StrategyCode` enum 확장 M00~M20. control_command/NAMING/codegen 일괄 확장.

## 3. 신규 정본 코드 (시뮬에 대응 전략 없음 — 진짜 DR 액션)

| 코드 | name_en | name_kr | 비고 |
|:--:|------|------|------|
| M16 | DR_NightSetback | DR 야간 셋백 | 능동 부하감축 셋백(setpoint↑). 시뮬 M00 baseline 의 야간 setback 과 구분(능동 DR) |
| M17 | LightingControl | 조명 제어 | 조명 디밍(lighting_pct↓). 시뮬에 조명 전략 부재 |
| M18 | ESSPeakShaving | ESS 피크셰이빙 | ESS 방전(ess_discharge). 시뮬에 ESS 부재 |
| M19 | DR_Integrated | DR 통합 최적화 | setpoint+조명+ESS 통합 DR. 시뮬 M14 Combined_Full 과 구분(ESS 포함) |
| M20 | DR_EmergencyCurtail | DR 긴급 감축 | 최대 감축. 시뮬 M15 Combined_Premium 과 구분 |

## 4. Behavior-preserving 재키잉 맵 (DR 도메인 old M-code → new)

| 구 DR 코드 | 구 DR 의미 | → 신 코드 | 근거 |
|:--:|------|:--:|------|
| M00 | 기준(무제어) | **M00** | 정본 Baseline 일치 |
| M02 | 외기냉방 | **M02** | 정본 Economizer 일치 |
| M04 | PMV 쾌적 | **M04** | 정본 PMV_Strict 일치 |
| M08 | 예냉(Pre-cooling) | **M09** | 정본 Precooling 으로 재지정 (정본 M08=HeatRecovery 아님) |
| M11 | (signal_dr economic) | **M11** | 정본 Combined_EMS — DR 라우팅에 정본 전략 사용, 유지 |
| M01 | 야간 Setback(DR) | **M16** | 신규 — 능동 DR 셋백 |
| M07 | 주간 조명 제어 | **M17** | 신규 — 조명 |
| M09 | ESS 피크셰이빙 | **M18** | 신규 — ESS |
| M14 | 통합 에너지 최적화(DR) | **M19** | 신규 — ESS 포함 DR 통합 |
| M15 | DR 긴급 감축 | **M20** | 신규 — 긴급 감축 |

### 4.1 signal_mapping 재키잉 (ems_strategies.json default)
- `signal_mapping`: NORMAL M07→**M17** · MODERATE M04→M04 · HIGH M14→**M19** · EMERGENCY M15→**M20**
- `signal_mapping_dr`:
  - NORMAL {reliability M01→**M16**, economic M07→**M17**}
  - MODERATE {reliability M04, economic M04}
  - HIGH {reliability M14→**M19**, economic M11}
  - EMERGENCY {reliability M15→**M20**, economic M14→**M19**}
- `reduction_schedule.json`: M00 유지 · M15→**M20**

## 5. 영향 아티팩트 (전수) + 실행 단계

| # | 아티팩트 | 변경 | 위험 |
|:--:|------|------|:--:|
| S1 | energy-contracts `ems_strategies.json` | #StrategyCode enum→M00~M20 · default.strategies M00~M15→NAMING 정합 + M16~M20 추가 · signal_mapping(_dr) 재키잉 | 낮음(스키마) |
| S2 | energy-contracts `control_command.json` | strategy enum M00~M15→M00~M20 | 낮음 |
| S3 | energy-contracts `reduction_schedule.json` | M15→M20 | 낮음 |
| S4 | `8.simulation/docs/NAMING_UNIFICATION.md §1.1` | M16~M20 행 추가(정본 이름 SSOT) | 낮음 |
| S5 | `gen_constants.py --all` | 전 consumer `_generated_constants` 재생성 | 낮음 |
| S6 | edge-agent `src/strategies.py` | 프리셋 재키잉(§4) | **배포** |
| S7 | gridbridge `src/ai_oracle.py` | M15→M20·M14→M19·M07→M17 | **배포** |
| S8 | be-3d `src/visualization/edge_control.py` | 프리셋 재키잉(§4) | **라이브 VWorld 데모 — 게이트** |
| S9 | ems_transformer PolicyVector enum + fixture mirror | enum M00~M20 수용(시뮬은 M16~M20 미생성) | 낮음 |
| S10 | agentleague | debate = 정본 M-code(시뮬 의미) + 본류 policy_vector(안 A) | 중 |

**실행 순서**: S1~S5(foundation, SSOT) → S9(ems 수용) → S6/S7(배포 repo, 각 PR+테스트) → **S8(라이브 데모, 사용자 cutover 게이트)** → S10(agentleague). 각 단계 `validate_ssot.py` + 회귀.

## 6. 검증 게이트
- `validate_ssot.py` PASS (4 repo) · `gen_constants.py --check` drift 0.
- 13/16 충돌 → **0** (재측정: 시뮬·DR 코드 의미 disjoint).
- agentleague→Layer3 spike 재측정(M-code 의미 단일화 후 파싱율 변화).
- edge-agent/gridbridge/be-3d 회귀(프리셋 resolve 동일 물리값 보존 — 코드만 변경).

## 7. Rollback
각 단계 독립 PR. S6~S8 배포 repo 는 git revert + 재배포. S1~S5 는 enum 축소(M16~M20 제거)로 원복(단 consumer 선롤백 후).

## 8. 실행 중 발견 — scope 대폭 확장 (2026-06-16, 실행 PAUSE 사유)

foundation(S1~S5)은 깔끔히 구현·validate_ssot PASS 했으나, consumer **code** 재키잉 착수 시 M-code 가 **§4 의 9개 파일보다 훨씬 광범위**하게, 그리고 **3차 의미 집합**까지 갖고 박혀 있음을 발견:

- **3차 의미 집합 (신규)**: be-3d `src/agents/a03_optimizer/agent.py` 는 M01=야간환기냉방·M07=열원우선순위·M08=CO2기반환기 — 시뮬 NAMING·DR 카탈로그 **둘 다와 다른** 또 하나의 의미. → 단순 재키잉 불가, 도메인 판단 필요.
- **edge-agent 추가 침투**: `agentleague/subscriber.py`(전략별 reward weight), `api/server.py`(`_VALID_STRATEGIES` set + 검증 메시지 ×2), `api/static/index.html`(UI), `drivers/{energyplus,virtual}.py`, `main.py`(긴급 dispatch M15/M14).
- **gridbridge 추가 침투**: `dispatch/engine.py`(signal_level→전략 map), **테스트 다수**(`test_ai_oracle`·`test_dispatch_builder`·`test_critics_gate`·`test_mqtt_bridge` 가 M07/M14/M15 하드코딩).
- **be-3d 추가 침투**: `shared/constants.py`(M-code EUI lookup 테이블, 시뮬 의미), `shared/reduction_schedule.py`, `simulation/buildwise/{mock_runner,validator}.py`, `visualization/control_intent.py`(정규식 M00~M15).

→ 배포된 DR dispatch + 라이브 VWorld 데모 + 테스트 스위트 + 옵티마이저(3차 의미)를 가로지르는 **수십 파일 multi-repo 작업**. 잘못된 의미 판단 시 배포 제어·데모 손상. **단일 sweep 불가 → §9 staged program 으로 재개 권고.**

## 9. Staged Program (재개 시)

repo·도메인별 독립 PR, 각 PR 자체 테스트 + 검증, 라이브 데모는 cutover 게이트:
1. **P0 — 의미 인벤토리 확정**: 전 repo M-code 참조를 {시뮬 / DR / 옵티마이저-3차 / EUI-data / UI / test} 로 전수 분류표 작성(본 §8 시드). a03_optimizer 3차 의미의 정본 매핑 결정.
2. **P1 — energy-contracts foundation** (S1~S5, 본 ADR 구현분 재적용) + validate_ssot. 단독 PR이되 consumer regen 동반(coupling).
3. **P2 — gridbridge** (코드 + 테스트 동시) PR.
4. **P3 — edge-agent** (strategies + server + subscriber + main + drivers + UI + 테스트) PR.
5. **P4 — be-3d 비-데모** (a03_optimizer 3차 의미 정합 + constants/reduction/buildwise) PR.
6. **P5 — be-3d 라이브 데모** (edge_control + control_intent) PR + **사용자 cutover 게이트 + 데모 회귀**.
7. **P6 — ems_transformer**(PolicyVector enum M20 + fixture) + **agentleague**(debate 정본 M-code + 안 A policy_vector).

> **대안(권고 검토)**: 본 통합의 *촉발 목적*인 agentleague→Layer3 통합은 **안 A(policy_vector 기반)** 로 M-code 이름 의존을 제거하면 본 대공사 없이 달성됨. 네임스페이스 통일은 그 자체로 가치 있으나 독립 program 으로 분리 가능.
