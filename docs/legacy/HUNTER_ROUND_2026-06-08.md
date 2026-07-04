# 사냥꾼 라운드 감사 기록 — 2026-06-08

> energy-contracts 전수 오류·개선 감사. 6 차원 멀티에이전트 finder + 건별 적대적 검증(refute).
> 결과 PR: **#10**(자체완결 34건). Deferred 3건 = [DEFERRED_INTEGRATIONS.md](DEFERRED_INTEGRATIONS.md).
>
> **상태(2026-06-08)**: PR #10 **MERGED** (전체 CI PASS). 동반 PR #9(REVIEW.md 배너) MERGED.
> **Deferred 3건(D-1/D-2/D-3) 전부 RESOLVED** (2026-06-08 후속) — 아래 [Deferred landing 완료](#deferred-landing-완료-2026-06-08) 참조.

## 요약

| 지표 | 값 |
|------|----|
| 확정 findings | 36 (HIGH 1 / MEDIUM 15 / LOW 20) |
| 기각 (적대적 검증) | 1 |
| 자체완결 fix (PR #10) | 34 |
| Deferred (cross-folder) | 2 + CORE_KEYWORDS enum |
| 결과 | 160 tests PASS · `validate_ssot --check all` PASS · `gen_constants --check` **drift 0** |

## HIGH (1)

- **H1 — gate cache fail-open** (`critics/gate.py`): `_signature` 가 멤버 ID 집합만 키로 써 per-allocation `reduction_kw`/SOC/조명/PMV 를 무시 → 같은 group/target/members + 다른 안전지표 dispatch 가 이전 PASS 를 stale cache hit 으로 받아 Safety 평가 없이 통과. 시그니처에 안전지표 포함 + `test_cache_miss_on_different_reduction_kw` 회귀 가드.

## MEDIUM — 자체완결 (PR #10)

| # | 영역 | 수정 |
|---|------|------|
| M1 | critics | **룰별 차등 safety**(사용자 결정): `critic_base.critical_rules` 신설, hard interlock(setpoint/SOC) 단건 FAIL→block, soft(조명/PMV) 단건 WARN |
| M2 | critics | CarbonCritic `FACTOR_PATTERN` val 그룹 `\d+(?:\.\d+)?` — 정수/1/5자리 배출계수 누락 해소 |
| M3 | esg | `compose_scope._override` NaN/Inf/음수/bool 가드 — `total_co2_kg` silent 오염 차단 |
| M5 | ssot | `check_generated_drift` 헤더-only 한계 docstring 명시(본문검증=`gen --check`) |
| M6 | ssot | `check_strategy_pattern_consistency` — common.json↔STRATEGY_PATTERN_EXPECTED↔codes 정합(dead 상수 활성화) |
| M7 | scripts | `gen_pydantic_models._resolve_external_refs` transitive $ref 재해소(2단계 cross-file ref 빌드 FAIL 방지) |
| M8 | schema | `legacy_ems_code_mapping` S2 `maps_to` M09→M08(description=Pre-cooling=M08, active mapping 일치) |
| M9 | schema | `hvac_ems_matrix` M07/M08/M09 구 넘버링(DCV/ERV/예냉)→정본(Lighting/Pre-cooling/ESS). 조명·ESS=HVAC무관 → 전 행 compatible(C/HE/HG 잘못된 infeasible 해소, F14 G-PE1 오차단 제거) |
| M10 | test | `test_frozen_checkpoints_pinned` — frozen 4 모델 checkpoint 정확값 pin(silent 교체 차단) |
| M11/M12 | test | safety 테스트 강화 — `block` 정확 단언 + zero-tolerance/soft WARN/public-mode 커버 |
| M13 | version | `__init__`(0.2.3)·pyproject(0.3.3)·CLAUDE(0.2.0) 3중 drift → 동기(0.3.4) + `test_version_consistency` |

## LOW (20) — 자체완결 (PR #10)

c_data 난독 `any()`/영문 커버 · MANDATORY_SIGNAL_LEVELS 주석 · retry overflow/decorrelated jitter · rate `int()`→`round()` · embodied_key 범위라벨 시작연도 · `DATA_SOURCE_LABELS`/`RUN_MODES`(가드로 대체) · `classify_tests` auth word-boundary(`test_engineering_session.py` 오부여 해소) · gen_pydantic 미설치 안내/exit code/docstring · `check_port_conflicts` 비-deployed 경고 · `hvac_ems_matrix` default↔required + `$ref`+`type:object` sibling · `_index.yaml` 31→58 전수등재 + `check_index_completeness` · `__init__`/CLAUDE 문서 stale.

## 기각 (1)

- **esg embodied_key post-2017 vintage 누락**: 함수 동작은 사냥꾼 주장대로이나, 검증관이 상류 be-3d `vintage_class` 어휘가 폐쇄 4값(`post-2010`→`post2017` 정상 매핑)임을 DB view/archetypes 로 확인 → "raw 연도(y2021) 입력" 전제가 시스템에 부재 → **INVALID**.

## 신설 가드 (재발 방지)

- `validate_ssot.check_strategy_pattern_consistency` (M6)
- `validate_ssot.check_index_completeness` (LOW)
- `test_version_consistency.py` (M13), `test_frozen_checkpoints_pinned` (M10)

## Deferred (cross-folder — coordinated consumer bump)

M4(`_usage`→hybrid), M7(`ems_strategies.legacy_mapping`), CLAUDE 20 CORE_KEYWORDS enumeration.
사유: gen-loaded schema/`gen_constants.py` 변경은 6 consumer regen 강제(SSOT hash cascade). 상세·절차 = [DEFERRED_INTEGRATIONS.md](DEFERRED_INTEGRATIONS.md).

## Deferred landing 완료 (2026-06-08)

3건 전부 해소. **PR 8개 머지**.

| Deferred | 해소 | PR |
|----------|------|-----|
| **D-1 (M4)** `_usage`→hybrid + `check_codegen_input_usage()` | energy-contracts v0.3.5 | EC #12 |
| **D-2 (M7)** `gcs_e_codes` E1/E2/E7/E10/E11 정정 + `check_legacy_code_consistency()` | energy-contracts v0.3.5 | EC #12 |
| **D-1/D-2 cascade** 6 consumer regen (hash `f462482943b38ce1`→`05d50c0601204d89`) | edge/gridbridge/agentleague/eduarena/be-3d | #13 / #8 / #6 / #17 / #130 |
| **D-3** 20 CORE_KEYWORDS enumeration + 로컬 가드 + verifier lock-step | energy-contracts v0.3.6 + ai-champion-2026 | EC #14 / ac #44 |

### 운영 학습 (coordinated bump 실전 — 재발 참조)

1. **Atomicity 강제**: 로컬 pre-commit `check_generated_drift` 가 EC↔consumer 를 **working-tree 수준**에서 일치 요구. EC schema 커밋하려면 consumer 파일도 regenerated 상태로 디스크에 있어야 통과(consumer 되돌리면 EC 커밋 차단).
2. **순서 고정**: consumer `ssot-drift` CI 는 `jukkim/energy-contracts` **master** 를 clone 해 `gen_constants --check` 비교 → **EC PR 선행 머지 필수**. EC 머지 전 consumer push 시 옛 hash 불일치로 CI 실패.
3. **EC PR 은 self-validate**: EC `ssot-check.yml` 의 consumer drift step 은 `if [ -d ../edge-agent ]` 가드 → CI(sibling 부재)에선 skip. EC PR 은 `validate_ssot --check all` 자체만 통과하면 머지 가능.
4. **be-3d 기본 브랜치 = `main`** (다른 5 repo 는 `master`). PR base 주의.
5. **WIP 브랜치 보호**: 사용자 WIP 브랜치(gridbridge/be-3d) 는 stash + master/main 기반 전용 브랜치 분리 또는 transient checkout 으로 **건드리지 않고** landing.
6. **D-3 lock-step 패턴**: sibling 에만 있던 SSOT 리스트를 본 repo 에 enumeration mirror + 양쪽 가드(본 repo 로컬 + sibling verifier 동기) → cross-folder 단독-검증-불가 항목의 표준 해법.
