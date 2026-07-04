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

<!-- MIRROR_CORE_KEYWORDS_BASE_V1 -->
> **20 BASE CORE_KEYWORDS (명시 enumeration)**: `G-PE1` `G-PE2` `G-PE3a` `G-PE3b` `F14` `/v1/policy-evaluate` `Policy Evaluation Contract` `counterfactual` `behavior_model` `policy_type` `Specialist Agent` `Ingestion Worker` `Edge Agent` `v1.9.2` `Inverse` `4-stack` `enforcement_level` `spec_only` `G-SR2` `tenant_regions.json`
<!-- /MIRROR_CORE_KEYWORDS_BASE_V1 -->
>
> ↑ SSOT = ai-champion-2026 scripts/verify_cross_folder_mirror_drift.py 의 BASE_KEYWORDS (본 enumeration 은 그 mirror). 본 repo 는 REVERSE 거점 아님 → BASE 20 만 요구 (REVERSE 8 은 be-3d/eduarena/ems_transformer). 로컬 가드 = scripts/validate_ssot.py 의 check_mirror_core_keywords (위 20 토큰이 본 헤더 본문에 전수 등장하는지 검증). 동기 가드 = ai-champion-2026 verifier 가 본 블록 ↔ BASE_KEYWORDS 동일 집합 강제.

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

## 규칙

1. **스펙 변경 시 반드시 이 프로젝트에 먼저 반영** → 각 프로젝트가 참조
2. 스키마 필드 추가는 자유, **필드 삭제/이름 변경은 금지** (하위 호환)
3. 각 프로젝트 CLAUDE.md에 이 프로젝트 참조 명시
4. 버전 태그로 호환성 관리: `v1.0`, `v1.1` (minor = 필드 추가, major = 호환 깨짐)
5. **변경 제안은 PR로**. VW/GB 측과 Edge 측 양쪽 리뷰 후 머지. 스펙에 없는 필드는 수신자가 무시(forward-compat).

## SSOT 변경 절차 (load-bearing)

스키마·상수 변경 시 **반드시 이 순서**로 진행한다 (`myjob/docs/SSOT_GOVERNANCE.md` 절차):

```
1. schemas/*.json 수정 (SSOT — 값·필드는 여기서만 정의)
2. python scripts/validate_ssot.py          # SSOT 위반 검사
3. python scripts/gen_constants.py --all     # Tier 3 자동 생성 (_generated_constants)
4. 각 consumer repo: pytest tests/test_ssot_consistency.py
5. commit (pre-commit hook 이 validate + gen_constants --check 재검증)
```

- **손편집 리터럴 금지**: 배출계수·PE·ZEB·시장가격 등 값은 `energy_contracts/schemas/` 단일 root 에서만 정의. consumer 는 `gen_constants.py --all` 생성본(`_generated_constants`) 을 파생.
- **필드 삭제/이름 변경 금지** (하위 호환). 필드 추가는 자유. 버전 태그: minor = 필드 추가, major = 호환 깨짐.
- 검증: `python scripts/validate_ssot.py`. 빌드: `.venv/Scripts/python.exe -m build --wheel`.

## Consumer / pin-lockstep (load-bearing)

5 consumer repo (**be-3d, edge-agent, gridbridge, agentleague, eduarena**) 는 `gen_constants.py --all` 로 Tier 3 자동 생성 + ssot-drift CI 검증. `agents`(ingestion-worker) 측만 wheel import 로 진입 — 동일 wheel SHA pin 으로 schema/model drift 차단.

- **EC pin lockstep** (`validate_ssot.py EC_PIN_CONSUMERS`): edge-agent / gridbridge / building-energy-3d 는 `pyproject.toml` 의 energy-contracts git pin 태그가 `_generated_constants` regen 버전과 lockstep. skew 시 CI 에서 jsonschema 가 신규 M-code 거부.
- pin bump / 신규 schema cascade 는 **schema 변경 시에만** 6-repo regen. reference-only schema(gen 미진입)는 hash cascade 없음.

## 사용 (wheel import)

```python
from energy_contracts import load_schema, list_schemas, SCHEMAS_DIR
from energy_contracts._pydantic_models.run_modes import RunMode
```

## 상세 (catalog / 아키텍처 / 버전 이력)

> 통신 경로 4개 · 수용가(VEN) 분류 · ESG 그룹 · 디렉토리 트리 · Phase C wheel · 작성 책임 분담 · **전체 버전 이력(v1.0~0.3.8)** · 참조 프로젝트 표 → **[docs/CLAUDE_DETAIL.md](docs/CLAUDE_DETAIL.md)** (2026-07-04 diet 로 분리, verbatim).
