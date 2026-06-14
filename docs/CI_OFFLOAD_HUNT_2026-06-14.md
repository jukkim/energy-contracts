# CI 4090 오프로드 — 사냥꾼 라운드 (2026-06-14)

> 트리거: 사용자 "github에 에러가 많이 발생했는데" + "최고 현상금 사냥꾼팀 투입해서 오류 찾아".
> 6 차원 헌터 × 13 repo + 적대적 검증 (Workflow `wf_75512bc0-6ff`, 31 agent, 22 confirmed).
> 관련 SSOT: `~/.claude/rules/github-actions-budget.md` · 메모리 `[[project_github_actions_budget_governance]]`.

## 1. 근본 원인 — **부분 오프로드 (partial offload)**

2026-06-14 오전 14 repo 의 CI 를 4090 self-hosted Linux runner 로 오프로드(`runs-on: ubuntu-latest` → `[self-hosted, Linux, X64]`)할 때, **각 repo 의 `test.yml`(pytest)만 옮기고 `ssot-drift.yml` 등 다른 워크플로를 `ubuntu-latest`(hosted)에 남겼다.** 커밋 메시지는 "전 워크플로 오프로드"라 주장했으나 사실이 아니었음.

GitHub Actions 월 한도가 **92%(1847/2000분)** 소진된 상태에서, hosted runner 에 남은 잔류 잡은 runner 할당이 거부되어 **steps 0개·로그 blob 부재·3~9초 instant-fail**(빨강)이 된다. self-hosted 로 옮긴 잡(분 소비 0)은 전부 녹색인 것과 대조 → 사용자 대시보드의 "많은 에러"의 실체.

**instant-fail 시그니처** (코드/테스트 실패와 구분): `conclusion=failure` + `steps=[]` + `runnerName=null` + 지속 ~3-9초 + 로그 blob 404. 한도 여유 시점(예: 06-11)의 동일 워크플로 run 은 전 step 정상 완주 → 워크플로 자체는 건강, runner 할당만 거부된 것.

## 2. 현황 진단 (13 repo)

- 기본 브랜치(master/main) HEAD **녹색 = 13 중 12**. 유일 라이브 빨강이던 `ems-transformer sentinel-cron`(매일 cron + hosted)은 본 세션에서 수정(PR #92, ↓).
- 나머지 빨강의 정체: ① `restore/full-ci-2026-07-01` **드래프트 PR**(의도적, 한도 리셋 후 머지) ② 어제 오프로드 실험 브랜치(superseded) ③ hosted 잔류 잡의 PR/schedule instant-fail.
- **라벨 격리 = 0 위반** (bare `runs-on: self-hosted` 전무, edge-agent Windows nightly `[self-hosted, Windows, mosquitto]` 격리 정상). BUG#1 클래스 깨끗.
- **PR 영구 블록 구조 부재** (어느 repo 도 self-hosted 필수 status check 가 branch protection 에 없음).

## 3. 확정 findings (22, 적대적 검증 통과)

### HIGH — 부분 오프로드 누락 (라이브 PR/schedule 빨강)

| repo | workflow | 내용 | 조치 |
|------|----------|------|------|
| building-energy-3d | `ssot-drift.yml` | 4 job 전부 hosted → PR마다 4빨강 | **PR #192** (4 job → self-hosted) |
| ingestion-worker | `ssot-drift.yml` | ssot-drift job hosted → PR 빨강 | **PR #36** |
| ems-transformer | `ssot-drift.yml` | verify_ssot_drift_combined hosted | **PR #93** |
| building-energy-3d | `e2e.yml` | Playwright 주1회 cron + hosted → 매주 빨강 | **defer** (↓ §4) |
| ai-champion-2026 | `cross_folder_drift_verify.yml` | hosted + **runner 미등록** → PR 빨강 | **defer** (↓ §4) |
| building-energy-3d | `frontend-ci.yml` | Node 빌드 hosted, main HEAD 빨강 | **defer** (Node 네이티브 한계) |

### LOW — 예산룰 준수 (schedule step-level `timeout-minutes` 누락)

`agentleague`·`eduarena`·`gridbridge`·`energy-contracts`·`edge-agent`·`ingestion-worker`·`building-energy-3d-lab`·`ems-transformer(sentinel-cron)` 의 schedule 워크플로가 step-level `timeout-minutes` 미설정. job-level 은 대부분 존재 → 분 누수 위험 낮음. paths-ignore 최소(`**.md`/`docs/**`)인 repo 다수(`building-energy-id`/`smartbuilding`/`reverse-ems` 등). → **배치 follow-up** (§4).

## 4. 본 세션 조치 vs Deferred

**조치 완료 (이번 세션):**
- `ems-transformer sentinel-cron.yml` → self-hosted (PR #92, 머지·검증 그린: self-hosted 에서 전 step success).
- `ssot-drift.yml` 부분 오프로드 완성 3 repo: be-3d #192 · ingestion-worker #36 · ems-transformer #93 (PR 자체 ssot-drift 체크가 self-hosted 에서 도는 것이 검증).

**Deferred (사유 명시):**

| 항목 | 사유 | 선행 조건 |
|------|------|----------|
| be-3d `e2e.yml` Playwright | basic noble runner 의 chromium 시스템 의존성(libnss3 등) `--with-deps` 실제 성공 미검증 | noble 에서 `playwright install --with-deps chromium` 1회 검증 후 오프로드, 아니면 schedule 제거(dispatch-only) |
| ai-champion-2026 `cross_folder_drift_verify.yml` | **로컬 클론 없음 + runner 미등록** | `setup_linux_runner.sh ai-champion-2026` 선등록 후 runs-on 변경. schedule 아님(PR시만 빨강) = 한도 리셋까지 admin merge 우회 |
| be-3d/agentleague frontend (Node 빌드) | `unrs-resolver` napi-postinstall code 127 = build-essential/native toolchain 부재 | richer runner 이미지 또는 hosted 유지 |
| building-energy-id 전체 (`ci.yml` 6 job) | postgres services·npm네이티브·docker-build·terraform·secret-scan | 전용 도구 runner (별 프로젝트) |
| reverse-ems `pytest.yml` | gitignore `checkpoints/` 모델파일 의존 = pre-existing 실패 (오프로드 무관) | CI provisioning step |
| schedule step-level `timeout-minutes` 8 repo | 예산룰 준수(LOW), job-level 존재로 누수 낮음 | 배치 PR (글로벌 룰 정합) |

## 5. 교훈 (영구)

- **오프로드는 repo 단위가 아니라 워크플로 단위**: `test.yml`만 옮기고 `ssot-drift.yml`/`e2e.yml` 등을 두면 부분 오프로드 = 한도 소진 시 그 워크플로만 instant-fail. **"전 워크플로 오프로드" 주장 전 `grep -rn 'ubuntu-latest' .github/workflows/` 전수 확인 의무.**
- ssot-drift 류(checkout + setup-python + inline 검사)는 services/docker/Node 의존 0 → noble runner 무수정 호환. Playwright/Node 빌드/postgres services 는 별도 검증·runner 필요.
- instant-fail(steps 0/runner null/~3초) ≠ 코드 실패. 진단 시 한도 여유 시점 run 과 비교해 회귀 여부 판정.
