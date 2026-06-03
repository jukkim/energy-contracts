# CLAUDE.md — Energy Contracts (공유 스펙)

> **SSOT**: ai_core_role_separation_plan v1.9.2 §6.5 — Policy Evaluation Contract. 본 repo = energy-contracts Tier 2 도메인 계약 허브. 본 폴더가 9 sibling repo (ems-transformer / ingestion-worker / edge-agent / building-energy-3d / gridbridge / agentleague / eduarena / energy-contracts / sim_campaign_2026) 의 schema/_pydantic_models/critics 단일 SSOT 를 제공한다. SSOT 본문 = `공모전/2026-04-24_AI챔피언_*/docs/ai_core_role_separation_plan.md` v1.9.2.
>
> **Gateway namespace (ADR-001)**: **F14** = `POST /v1/policy-evaluate` Policy Evaluation Contract 4 단계 (intake → counterfactual → aggregation → dual_sign_off). 본 repo 의 `policy_evaluation_contract.json` schema 가 F14 endpoint 의 request/response 계약. F12/F13 = internal proxy + Claude LLM (별 SSOT).
>
> **Gates (G-PE 4종)**: **G-PE1** (intake validation) · **G-PE2** (LLM hedging lint 52 사전) · **G-PE3a** (bootstrap N≥1000) · **G-PE3b** (sign-flip rate ≤ 20%). 본 schema 의 `behavior_model` + `policy_type` 필드가 G-PE1 entry condition.
>
> **Inverse Decision System (§6.4)**: **4-stack** (multi-modal input + behavior_model + counterfactual + Forward-Inverse Consistency Loss). 본 repo 의 critics/ 4종 (Legal/Carbon/Safety/Data) + CriticsGate = 4-stack 의 검증 layer.
>
> **Agent 어휘 4 종 (v1.9.2 §0.9)**: **Specialist Agent** (Layer 1 A1~A14 building-energy-3d) · **Ingestion Worker** (백그라운드 ETL ingestion-worker repo) · **Dev Subagent** (Claude Code 개발 보조) · **Edge Agent** (OpenADR/IEEE 2030.5 표준, edge-agent repo). 단독 "agent" 사용 금지, 종류 prefix 의무.
>
> **SR-2 Multi-tenant RLS (2026-06-03 신설, Ultracode `wf_2a6728f8-fc2`)**: `tenant_regions.json` v1.1-draft (sibling `projects/ingestion-worker/docs/tenant_regions.v1.1.draft.json`) 의 `TenantEntry.enforcement_level` enum SSOT = `{spec_only, enabled, deprecated}` (Conservative 초안의 `{strict, warn, off}` 폐기). **G-SR2-1 ~ G-SR2-7** 7 게이트 진입 = 모두 사용자 명시 트리거 의무 (case #1 destructive + case #2 cross-folder + case #3 영구 architectural). G-SR2-1 = 본 energy-contracts repo 의 `tenant_regions.json` schema v1.0 → v1.1 promote + 5 consumer (`edge-agent`/`gridbridge`/`agentleague`/`eduarena`/`building-energy-3d`) `gen_constants.py --all` regen atomic. 본 repo v1.1 promote PR = 사용자 트리거 PR #8 (campaign DEFERRED §SR-2.6). 본 시점 `tenant_regions.json` v1.0 = `enforcement_level` 필드 부재, sibling draft 가 SSOT. 본 schema 의 audit 대상 9 테이블 매트릭스 = sibling SR_2_RLS_MULTITENANT_SPEC.md §3.1.
>
> 본 mirror 헤더는 ai-champion-2026 의 `verify_cross_folder_mirror_drift.py` lock-step gate 정합용 — **20 CORE_KEYWORDS** 포함 (v1.9.2 16 + SR-2 4 추가 2026-06-03). SSOT 갱신 시 본 헤더도 동시 갱신 의무.

> **SSOT 허브** — Tier 2 도메인 계약. 변경 시 `myjob/docs/SSOT_GOVERNANCE.md` 절차 준수. 검증: `python scripts/validate_ssot.py`.
> **외부 의존 작업 (2026-05-26, agents arch A5 3-tier 분류 확정)**: agents `src/ingestion/_schemas/__init__.py` 의 3-tier SSOT 분류에 따라 — **Tier 1 (wheel)**: `drift_report`, `retrain_request` 2건 (sibling read/receive 대상, 미작성). **Tier 2 (local, wheel 진입 X)**: `negotiation_decision`, `post_validation_result`, `auto_retrain_policy` (agents-only, `45a99e8` commit). **Tier 3 (jsonb)**: `audit_event.extra`. 본 repo Tier 1 wheel 후보는 **`drift_report`, `retrain_request`** 2건 — DriftMonitor/RetrainOrchestrator 가 sibling 으로 emit/receive 진입 시 trigger. retrain_jobs queue 자체는 agents DB schema 009 + smartbuilding W7-ext (`545755a`) polling consumer 로 처리, wheel 불요. 명세: agents `src/ingestion/_schemas/__init__.py` + `docs/PHASE_DI_PLAN.md §4.5`.

## 목적

VWorld(L1), GridBridge(L2), EdgeAgent(L3) 3개 프로젝트 간 **인터페이스 계약서**.
각 프로젝트는 이 스펙을 참조하여 독립 개발하되, 호환성을 보장한다.

**이 프로젝트는 스펙 + 도메인 중립 SSOT 코드를 둔다. 도메인별 결정·실행은 각 프로젝트에서 한다.**

## 이 패키지에 무엇이 와야 하는가 (3 카테고리)

본 패키지는 다음 3 카테고리 중 하나에 해당하는 자산만 받는다. 의문 시 `myjob/docs/SSOT_GOVERNANCE.md` §9.2 의 Q1~Q4 진입 판정을 적용:

| 카테고리 | 위치 | 예 |
|---------|------|------|
| **스키마** | `energy_contracts/schemas/*.json` | 50+ JSON Schema (DR 이벤트, 텔레메트리, 배출계수, 건물 archetypes 등) |
| **상수 / 모델** | `energy_contracts/_pydantic_models/*.py`, `_utils/*.py` | 자동 생성 Pydantic, `redact_pnu` |
| **도메인 중립 룰 / 검증 / 조합자** | `energy_contracts/critics/*.py`, `_utils/*.py` | 4 종 Critic + CriticsGate (2026-05-27 신규) |

### 진입 거절 사례

| 안티 패턴 | 거절 이유 |
|----------|----------|
| `dr_critics_gate.py` (도메인 이름 박힘) | 다른 도메인 재사용 불가 → `critics/gate.py` 로 |
| `dispatch_engine.py` (실시간 결정 로직) | GB 가 실시간 owner — 도메인 폴더에 |
| `building_energy_eui_calculator.py` (외부 DB 의존) | 외부 시스템 호출 — 인프라 분리 → 도메인 폴더에 |
| `carte_renderer.py` (UI 렌더링) | C 계층 — be-3d / frontend repo 에 |

## 통신 경로 (4개)

```
경로 0: 사용자 → VW     (브라우저/음성/텔레그램/카카오톡)
경로 1: VW → GB → EA   (ESG/DR 그룹 제어)
경로 2: VW → EA         (개별 건물 직접 제어)
경로 3: EA → VW         (직접 텔레메트리/알림)
경로 4: EA → GB → VW   (그룹 텔레메트리 집계)
```

```
사용자 (브라우저 🖥️ / 음성 🎤 / 텔레그램 💬 / 카카오톡 💬)
  │ 경로 0
  ▼
VWorld (L1) ──경로1──→ GridBridge (L2) ──→ EdgeAgent (L3) ×N
  │                                            │
  ├──────────경로2 (직접)─────────────────→     │
  │                                            │
  ◀──────────경로3 (직접 피드백)────────────     │
  ◀──────────경로4 (GB 경유)──── GridBridge ◀───┘
```

## 규칙

1. **스펙 변경 시 반드시 이 프로젝트에 먼저 반영** → 각 프로젝트가 참조
2. 스키마 필드 추가는 자유, **필드 삭제/이름 변경은 금지** (하위 호환)
3. 각 프로젝트 CLAUDE.md에 이 프로젝트 참조 명시
4. 버전 태그로 호환성 관리: `v1.0`, `v1.1` (minor = 필드 추가, major = 호환 깨짐)
5. **변경 제안은 PR로**. VW/GB 측과 Edge 측 양쪽 리뷰 후 머지. 스펙에 없는 필드는 수신자가 무시(forward-compat).

## 수용가(VEN) 분류 용어

이 플랫폼은 수용가를 운영 모드 기준으로 이분한다:

| 분류 | 한글 용어 | 영문 용어 (스키마 `kind`) | 대표 예 | 제어 가능 | 데이터 |
|------|---------|--------------------------|--------|:---:|------|
| 관측형 수용가 | Telemetry VEN / Observable | `telemetry` | 편의점 220채 (DB replay) | X (read-only) | 단일 채널 시간별 |
| 제어형 수용가 | Dispatchable VEN | `dispatch` | E+ 가상, 실 설비(BACnet/Modbus) | O (양방향) | 다채널, Tier A 15+ 필드 |

GridBridge는 `venue.kind` 에 따라 `gridbridge/command/*`·`schedule/*` 발행을 분기(관측형 스킵). 구현 기술은 `backend: replay|energyplus|real_bas|virtual` 로 별도 기술한다.

### ESG 사전 정의 그룹

| group_id | 이름 | kind | 수량 | 용도 |
|----------|------|:---:|:---:|------|
| `ESG-STORE-100` | 편의점 100 (에너지) | telemetry | 100 | 실측 벤치마크 |
| `ESG-STORE-120` | 편의점 120 (센서) | telemetry | 120 | 센서 분석 |
| `ESG-EP-OFFICE` | E+ 가상 오피스 | dispatch | N | 제어 검증 |
| `ESG-EP-APT` | E+ 가상 아파트 | dispatch | N | 제어 검증 |

## 디렉토리 (2026-05-19 — Phase C 재배치)

```
energy-contracts/
├── CLAUDE.md              ← 이 파일
├── pyproject.toml         ← 패키지 정의 (Phase C 신규, a12 wheel)
├── energy_contracts/      ← Python 패키지 진입점 (Phase C 신규)
│   ├── __init__.py              — load_schema(), list_schemas(), SCHEMAS_DIR
│   ├── schemas/                 ← JSON Schema (SSOT) — wheel package data
│   │   ├── common.json               — 공용 enum·패턴 (Strategy M00~M15)   [v2.0]
│   │   ├── ems_strategies.json       — EMS 전략 코드표 + DR매핑 + 레거시   [v2.0 신규]
│   │   ├── emission_factors.json     — CO2 배출계수 (KR/ID, Scope 1/2)     [v2.0 신규]
│   │   ├── energy_constants.json     — PE factor, ZEB, 등급, 기후 기준값   [v2.0 신규]
│   │   ├── market_prices.json        — KAU, SMP, 전기요금, REC, PPA        [v2.0 신규]
│   │   ├── building_archetypes.json  — B01~B17, 용도매핑, EUI, 리트로핏    [v2.0 신규]
│   │   ├── region_codes.json         — C01~C11, H_A~H_G, 일사량            [v2.0 신규]
│   │   ├── dr_event.json             — DR 이벤트 (GB 생성)
│   │   ├── reduction_schedule.json   — 감축 스케줄 (VW/GB → Edge)
│   │   ├── control_command.json      — 제어 명령 (VW/GB → Edge)
│   │   ├── telemetry.json            — 텔레메트리 (Edge → GB/VW)
│   │   ├── venue.json                — 수용가 레지스트리 (GB SSOT)          [v1.1]
│   │   ├── virtual_prosumer.json     — E+ 가상 수용가 I/O 계약 (Edge)       [v1.0]
│   │   ├── control_response.json     — 제어 결과 (Edge → GB/VW)             [v1.0]
│   │   ├── edge_registration.json    — Edge 자동 등록 메타 (Edge → GB)      [v1.1]
│   │   └── edge_status.json          — heartbeat + 설비·드라이버 (Edge)     [v1.0]
│   └── _pydantic_models/        ← 자동 생성 모델 (Phase C 이동)
│       └── run_modes.py              — RunMode/AuthPolicy/DataScope enum
├── scripts/               ← 도구 (path 갱신: SCHEMAS_DIR = energy_contracts/schemas/)
│   ├── gen_constants.py             — Tier 3 자동 생성기
│   ├── validate_ssot.py             — SSOT 위반 검사
│   ├── gen_pydantic_models.py       — schemas → _pydantic_models 자동 생성
│   └── classify_tests.py            — test_classification.json 적용
├── protocols/             ← 프로토콜 규칙
│   ├── broker-architecture.md    — MQTT 브로커 배포·인증·Edge 유형 (VW)
│   ├── mqtt-topics.md            — 토픽·QoS·retain·ACL·네이밍 (통합)
│   └── openleadr-profile.md      — OpenADR 프로파일 (레거시)
├── openapi/               ← API 스펙 (미정)
├── examples/              ← 예제 JSON
└── tests/                 ← scripts 단위 테스트
```

## Phase C — wheel 배포 (a12, 2026-05-19)

`agents` Track 의 a12 결정에 따라 패키징 추가. `building.energy-3d` 와 `agents` repo 가 동일 wheel SHA pin 으로 schema/model drift 차단.

**사용**:
```python
from energy_contracts import load_schema, list_schemas, SCHEMAS_DIR
from energy_contracts._pydantic_models.run_modes import RunMode

run_modes = load_schema("run_modes")           # dict
all_schemas = list_schemas()                   # ['agent_contracts', ...]
```

**빌드**:
```bash
.venv/Scripts/python.exe -m build --wheel    # → dist/energy_contracts-0.1.0-py3-none-any.whl
```

**기존 `_generated_constants` 패턴과 공존**: 5 consumer repo (be-3d, edge-agent, gridbridge, agentleague, eduarena) 는 그대로 `gen_constants.py --all` 로 Tier 3 자동 생성 + ssot-drift CI 검증 (변경 없음). agents 측만 wheel import 로 신규 진입.

## 작성 책임 분담

| 영역 | 작성 주체 | 리뷰어 |
|------|:---:|:---:|
| dr_event · reduction_schedule · control_command · broker-architecture | VW/GB 팀 | Edge 팀 |
| telemetry(보강) · control_response · virtual_prosumer · edge_registration · edge_status | Edge 팀 | VW/GB 팀 |
| mqtt-topics (통합) · venue · CLAUDE.md | 양쪽 공동 | 전원 |

## 버전

| 버전 | 날짜 | 변경 |
|:---:|:---:|------|
| v1.0 | 2026-04-19 | 초기 스펙: 감축 스케줄, DR 이벤트, 텔레메트리, 제어 명령 |
| v1.1 | 2026-04-19 | **관측형/제어형 이분화**. Edge측 스펙 4종 추가(virtual_prosumer, control_response, edge_registration, edge_status). venue.json 신설(kind+backend). mqtt-topics에 fleet/register · ACL · ven_id 네이밍 추가. |
| v2.0 | 2026-05-16 | **4-Module SSOT 확장**. EMS 코드 M0~M8→M00~M15 (16전략). 6개 공유 스키마 신설: ems_strategies(전략코드표), emission_factors(배출계수), energy_constants(PE/ZEB/등급), market_prices(시장가), building_archetypes(건물유형·EUI), region_codes(도시·HVAC). Layer 0(ENERGY_SSOT.md)→Layer 1(이 프로젝트)→Layer 2(각 프로젝트 constants) 3계층 거버넌스 확립. |
| v2.0.1 | 2026-05-16 | **통합 전략표 확정**. BuildWise+DR 의미 충돌 해소. M00=Baseline 공통화. 16 전략 단일 코드표: BuildWise(M00~M06,M11~M13), DR Control(M00,M01,M02,M04,M07~M09,M14~M15). M10=reserved. |
| v2.0.2 | 2026-05-20 | **`_utils.redact_pnu` 추가** (Phase E #5, E8). PNU PII redaction cross-repo SSOT — ems_transformer + be-3d 의 동일 함수 중복 제거. commit `c660812`. consumer 측은 wheel SHA bump 후 `from energy_contracts._utils import redact_pnu` 로 전환. 신규 단위 8 PASS. |
| v2.0.3 | 2026-05-22 | **`ai_model_registry` ecmhs 등재** — Phase 0-A baseline. ECMHS MPC 서로게이트(:8050) 모델 카드 추가. commit `6a7d755`. |
| v2.0.4 | 2026-05-24 | **KI-031 i18n + CSP 보강** — control/auth i18n 키 9 신규 + control optgroup 키 7 신규 (F-09). CSP 4 directive 추가 + `script-src 'unsafe-inline'` 제거, vworld/unpkg 화이트리스트. commits `29421fd`, `efb676f`, `9fa7f88`. |
| v2.0.5 | 2026-05-24 | **`korea_buildings` 정정** — 627만 → **729만** (VWorld footprint DB 실측 7,293,517). 전국 건물 카운트 SSOT 갱신. commit `0e91f67`. ~~외부 의존 note 추가 — agents Phase DI W12 진입 시 conflict_policy.json + negotiation_decision.json 신설 예정~~ → **v2.0.6 에서 정정**. |
| v2.0.6 | 2026-05-25 | **외부 의존 note 정정 (arch A11)** — agents `PHASE_DI_PLAN.md §4.5` 3-tier SSOT 결정에 따라 `conflict_policy` + `negotiation_decision` 은 agents local Tier 2 로 확정 (wheel 진입 X). agents commit `45a99e8` 에서 `policies/conflict_policy.yaml` local SSOT 신설 완료. 본 repo Tier 1 wheel 신규 후보는 별개로 **`drift_report`, `retrain_request`, `auto_retrain_policy`** 3건 (agents Phase DI 진행 시 trigger). |
| v2.0.7 | 2026-05-26 | **arch A5 3-tier 분류 확정 — `auto_retrain_policy` Tier 2 재분류** — agents `src/ingestion/_schemas/__init__.py` 가 명시한 분류에 따라 `auto_retrain_policy` 는 wheel 후보에서 제외, agents local Tier 2 로 확정 (`negotiation_decision`, `post_validation_result` 와 동일 계층). 본 repo Tier 1 wheel 후보는 **`drift_report`, `retrain_request`** 2건으로 축소. retrain_jobs queue 자체는 agents DB schema 009 + smartbuilding W7-ext (`545755a`) polling consumer 로 처리, wheel 불요. 보조 노트: agents/be-3d wheel pin `c660812` (2026-05-20) 이후 본 repo 12 commit 진행 (`83dc459`/`b0faa13` ai_model_registry v1.1, `316d857` security_policy v1.1, `0de924f`/`a71ebba` rq_ai_intent, `29421fd`/`efb676f`/`9fa7f88` KI-031, `0e91f67` korea_buildings 정정 등) — pin bump 는 consumer 측 trigger 대기. |
| **0.2.0** | **2026-05-27** | **critics 패키지 신설 (SSOT_GOVERNANCE §9 도메인 횡단 분리)** — `energy_contracts/critics/` 신규 (4 Critic + CriticsGate 조합자). be-3d `src/critics/` + `src/agents/dr/critics_gate.py` 이동. lockstep: be-3d import 마이그 + GB realtime owner wire-up (`POST /api/v1/dr/debate/{event_id}` 신설, be-3d 와 동일 path). 18 신규 EC tests + 9 신규 GB tests PASS, be-3d/GB 회귀 0. |

## 참조하는 프로젝트

| 프로젝트 | 경로 | 역할 |
|---------|------|------|
| VWorld (M1) | `projects/building-energy-3d/` | L1 — 스케줄 생성, 시각화, 직접 제어(경로2), 텔레메트리 수신(경로3) |
| GridBridge (M1) | `projects/gridbridge/` | L2 — 스케줄 배분, DR 정산, 텔레메트리 집계(경로4) |
| EdgeAgent (M2) | `projects/edge-agent/` | L3 — 스케줄 실행, 텔레메트리 발행(경로3,4) |
| AI Engine (M3) | `8.simulation/` | 배출계수·EMS전략·건물유형·PE factor 참조 (v2.0) |
| Agent Platform (M4) | 신규 (아이로) | 전략코드·등급·시장가·리트로핏 참조 (v2.0) |
