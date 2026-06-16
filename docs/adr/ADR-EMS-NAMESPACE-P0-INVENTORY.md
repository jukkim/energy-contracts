# P0 — M-code 의미 전수 분류 인벤토리 (ADR-EMS-NAMESPACE-UNIFY 선행)

> 2026-06-16, staged program P0. 3 repo 병렬 전수 조사(edge-agent / gridbridge / building-energy-3d). **결론: M00~M15 가 4+ 개 비호환 live 의미집합으로 오버로드** — 단순 재키잉 불가, 도메인 결정 다수 필요.

## 발견된 의미집합 (live·functional)

| # | 의미집합 | 대표 정의 위치 | M07 예시 | 비고 |
|:--:|------|------|------|------|
| 1 | **SIM (정본 NAMING §1.1)** | `8.simulation/docs/NAMING_UNIFICATION.md` | DCV(수요제어환기) | 352K 시뮬·학습모델·ems_transformer |
| 2 | **DR 프리셋** | edge-agent `strategies.py`, be-3d `edge_control.py`/`control_router.py` | 조명 제어(lighting_pct=60) | 배포 DR 제어 + 라이브 데모 |
| 3 | **OPTIMIZER-3차** | be-3d `agents/a03_optimizer/agent.py` | **열원 우선순위** | M01~M13 전부 독자 의미. golden snapshot 잠금 |
| 4 | **EUI-DATA** | be-3d `shared/constants.py`, `buildwise/mock_runner.py`, `building_archetypes.json` | (M07 행 없음) | M-code 키 숫자 EUI 테이블 (M00~M06,M11~M13만) |
| 5 | **드리프트 "SIM" 표** | be-3d `constants.py STRATEGY_NAMES` | 조명/콘센트 | NAMING §1.1 과도 불일치(M07≠DCV) — 정본 아님 |
| 6 | **UNKNOWN(active-bits)** | be-3d `rq_ai.py`, `test_ai_output_api` | `"M00,M13"` multi-hot | 단일전략 의미 아님 |
| ⚠ | **기존 mislabel 버그** | be-3d `tests/fixtures/p1_cached_scenarios.json` | M01="Economizer"(틀림) | 마이그레이션 무관 선재 버그 |

**최악 충돌**: M07 = SIM:DCV / DR:조명 / a03:열원우선순위 (3-way). M08 = SIM:HeatRecovery / DR:예냉 / a03:CO2환기 (3-way). a03 는 M01~M13 **전부** SIM 과 다른 의미.

## 재키잉을 막는 hard 장애물 (단순 치환 불가)

- **a03_optimizer 3차 의미**: M01~M13 독자 taxonomy 가 `pct` 절감선택·top-3 추천 구동 + **golden snapshot**(`tests/unit/snapshots/a03_optimizer/*.json`, "축열 최적화 (M13) — 9.0%")에 잠김. 정본 매핑 = **도메인 결정 필요**(a03 가 별 코드를 써야 하나?).
- **metric level 인코딩**: edge-agent `metrics.py`/`heartbeat.py` 가 `int(strat[1:])` 로 코드 숫자를 Prometheus gauge level 로 변환 → 재키잉 시 지표 값 의미 변동.
- **DB CHECK 제약**: gridbridge `db/migration_2026_05_phase4_dr.sql` 의 `strategy ~ '^M(0[0-9]|1[0-5])$'` — 마이그레이션 SQL 필요.
- **테스트 스위트**: 3 repo 합쳐 ~40+ 테스트 파일이 M04/M07/M14/M15 등 하드코딩(assertion). 재키잉 시 동시 갱신.
- **UI**: edge-agent index.html / gridbridge control.html·index.html / be-3d frontend dropdown 값.
- **regex 검증**: 여러 `^M(0[0-9]|1[0-5])$` 패턴(router·control_router·policy_vector.ts).

## 규모 (실측)

| repo | functional source 사이트 | 테스트 파일 | UI/기타 |
|------|:--:|:--:|------|
| edge-agent | ~25 (presets·validation·drivers·metrics·scheduler·dispatch) | ~25 | index.html·onsite·scripts |
| gridbridge | ~8 (ai_oracle·engine·router·DB) | ~6 | control/index/dashboard html |
| be-3d | ~30 (3 의미집합 혼재·EUI·optimizer·policy) | ~20 (golden 포함) | frontend picker/control |

→ 총 **~100+ functional 사이트 + ~50 테스트 파일**, 3 배포 시스템 + 라이브 데모 가로지름.

## P0 판정

1. **단일 sweep 절대 불가** — 4+ 의미집합이 같은 코드에 live. 코드별·파일별 의미 판정 필요.
2. **a03_optimizer 3차 의미 = 선결 도메인 결정**(별 namespace? 정본 흡수?) — golden snapshot 재기준 동반.
3. **드리프트 "SIM" 표(be-3d constants.py)도 정본 NAMING 과 불일치** — SIM 측조차 내부 드리프트.
4. 본 통일은 **수주 규모 독립 엔지니어링 program** + 배포/데모/CI 회귀 실위험.

## P4 a03_optimizer 결정 (사용자 "본질적으로 해결", 2026-06-16)

**결정 = a03 을 자체 네임스페이스 `OM00~OM13` (optimizer-measure) 로 분리** — a03 은 EMS 제어 전략이 아니라 **절감 조치 추천(% 측정)** 이라 개념이 다른 객체. EMS M-code 공간에서 완전 디커플 → M07/M08 3-way 충돌 근본 제거.

**a03 footprint (재키잉 M00~M13 → OM00~OM13, EMS M-code 와 무관해짐)**:
- `src/agents/a03_optimizer/agent.py`: `STRATEGY_SAVINGS`(14) + `SETBACK_DEPENDENCY`(M01/M05/M09) + 제외 set(M06/M11/M12, M00).
- `src/agents/core/mock_data.py`: a03 추천 echo (M05/M06/M10/M11/M13).
- **golden snapshots** `tests/unit/snapshots/a03_optimizer/*.json`: "축열 최적화 (M13)" 등 → OM 재기준.
- 테스트: `test_a03_optimizer`·`test_agents_core`(output_strategies=[M03,M06,M11,M12,M13])·`test_agents_pipeline`(M01).
- frontend a03 결과 표시(있으면).
- ⚠ a03 코드가 edge_control(DR)/sim 으로 흐르지 않음(P0 확인) → 분리는 be-3d 내부 contained. OM 은 EMS enum(`#StrategyCode`)과 별개 — 신규 `optimizer_measure` enum 또는 단순 prefix.

**P4 나머지 be-3d 비-데모 (정본 정합)**:
- `constants.py STRATEGY_NAMES`(드리프트 SIM: M07=조명) → **TRUE 정본 NAMING**(M07=DCV) 정합.
- `policy_savings.py`/`policy_llm.py`/`f14_analysis.py` POLICY_LEVERS(SIM) → 정본 의미 확인·정합.
- EUI 테이블(`constants.py`·`buildwise/mock_runner.py`·`building_archetypes.json`): M00~M06,M11~M13 = SIM 제어전략 키, 정본 유지(라벨 주석만 정합).
- `buildwise/validator.py` HVAC×M-code feasibility(SIM).
- frontend `policy_picker.ts`·`policy_vector.ts`(SIM, M00~M15 valid).
- 테스트 동반.

**P5 (별 게이트)** = be-3d 라이브 데모 `edge_control.py`(DR 프리셋, edge-agent 와 동일 M16~M20 재키잉)·`control_router.py`·`control_intent.py` + 데모 cutover.

## 권고 (P0 결론)

- 본 P0 인벤토리를 네임스페이스 통일 program 의 **scoping SSOT** 로 보존.
- **원 목적(agentleague→Layer3 통합)은 안 A(policy_vector 기반)로 분리 달성** — 본 대공사 불요.
- 통일 program 은 별도 우선순위로 착수 시 본 P0 → P1(foundation) → P2~P6 순. a03 3차 의미 결정이 P1 선행.
