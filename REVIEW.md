# energy-contracts 리뷰 로그

스키마/프로토콜 변경 시 리뷰 결과를 여기에 기록한다.  
양쪽 팀이 확인 → 합의 → 수정 → 체크 표시.

---

## 2026-04-19 v1.1 리뷰 (GPT-4o + VW 팀)

### HIGH

| # | 이슈 | 파일 | 상태 |
|---|------|------|:---:|
| H-1 | `strategy`가 control_command에선 required, control_response에선 optional — 충돌처럼 보이나 `status=failed`일 때 전략 미적용 가능 → **description에 의도 명시** 필요 | control_command.json, control_response.json | [x] |

### MEDIUM

| # | 이슈 | 파일 | 상태 |
|---|------|------|:---:|
| M-1 | `strategy` 정의가 enum (command) vs pattern (response) 혼용 → **enum으로 통일** 또는 `$defs`에 공통 정의 후 `$ref` | control_command.json, control_response.json | [x] |
| M-2 | `kind`, `backend`, `building_type` enum이 edge_registration + venue + virtual_prosumer에 각각 정의 → **`$defs/common.json` 분리** 검토 | edge_registration.json, venue.json, virtual_prosumer.json | [x] |
| M-3 | `dr_event.end_time`이 CANCELLED 시 무의미할 수 있음 → **description에 "취소 시 원래 예정 종료 시각" 명시** | dr_event.json | [x] |

### LOW

| # | 이슈 | 파일 | 상태 |
|---|------|------|:---:|
| L-1 | `constraints` 내 필수 필드 없음 — 의도적(모두 기본값)이면 description 추가 | control_command.json | [x] |
| L-2 | edge_registration v1.1 / venue v1.1 동시 버전업이지만 관계 문서 없음 → **CHANGELOG.md에 관계 기록** | edge_registration.json, venue.json | [x] |

### Edge 팀 처리 결과 (2026-04-19)

| # | 처리 방식 | 비고 |
|:-:|-----------|------|
| H-1 | `control_response.strategy.description` 에 "status=failed/rejected 시 생략 허용" 명시. `control_command.strategy.description` 에도 대칭 상호참조. | 두 파일 모두 description만 변경(호환성 무영향) |
| M-1 | `schemas/common.json` 신설하여 `$defs/Strategy`(enum) + `$defs/StrategyPattern`(pattern) 공통 정의. 각 스키마는 **inline enum 유지 + description에 common.json 동기화 명시**. | $ref 크로스 파일은 테스트 복잡도 증가 이슈가 있어, SSOT 문서화 + inline 복제 유지 절충안 채택. 향후 합의 시 $ref 전환 가능. |
| M-2 | 동일 — `common.json §Kind · §Backend · §BuildingType · §EdgeType · §SignalLevel` 공용 정의. 각 스키마 description에 "common.json §X SSOT 와 동기화" 마커. | 변경 시 양쪽 동시 수정 원칙 명시 |
| M-3 | `dr_event.end_time.description` — "CANCELLED 시에도 원래 예정 종료 시각을 그대로 보존(참고용). 실제 종료는 updated_at 로 추적" | 의미 보존 원칙 |
| L-1 | `control_command.constraints` 에 object 설명 + 각 필드 기본값·단위 서술. required 없음이 의도적임을 명시. | |
| L-2 | `CHANGELOG.md` 신설. v1.1 섹션에 `edge_registration v1.1 ↔ venue v1.1` 동기 관계 "둘 중 하나만 bump 금지" 명시. | v1.0 이력도 소급 기재 |

### VW 팀 최종 수락 (2026-04-19)

**6건 전부 수락.** Edge 처리 방식 동의.
- M-1/M-2 절충안 (inline 유지 + common.json SSOT) 합리적. 스키마 20개 넘으면 $ref 전환 재검토.
- common.json 추가로 스키마 10개 체제.
- **v1.1 finalize 완료.**

### 합의 프로세스

1. 리뷰 결과를 이 파일에 기록
2. Edge 팀: `[x]` 체크 + 처리 방식 기록
3. VW 팀: 수락/반론
4. 양쪽 수락 → finalize

---

## 2026-04-19 라운드 2 — Phase B+ 구현 후속 문서 동기화 (Edge 팀 제안)

Edge 측 Phase B+ 가 구현·실측 검증까지 완료된 시점에서, **VW·GB 프로젝트 내 문서**가 아직 갱신되지 않아 스펙 이행 상태와 내부 문서 간 괴리가 있다. Edge 팀 관할 밖이라 PR 은 못 올리지만, 본 리뷰 라운드로 각 팀에 공식 요청을 기록한다.

### HIGH

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| H2-1 | VW `docs/PRD.md` 에 관측형/제어형 수용가 시뮬레이션 섹션(§5.11 또는 유사)이 부재 — Phase CS(편의점 220 + E+ 가상) 기능 요구사항을 정식 PRD 엔트리로 추가 | VW | [x] `0f465c6` Phase CS 섹션 추가 |
| H2-2 | VW `docs/4-LAYER-ARCHITECTURE.md` 에 `venue.kind × backend` 이원 분류가 반영 안 됨 — §9 수용가 이분화 섹션(GB 라우팅 분기·ESG 그룹 4종·가상 PNU 규칙) 추가 필요 | VW | [x] `0f465c6` §9 신설 |
| H2-3 | GB `docs/DESIGN.md` 가 아직 없음 — 이번 세션에 구현된 MqttBridge·AI Oracle·kind 라우팅·DR dispatch→MQTT 자동 전파를 정식 설계문서로 고정 필요 | GB | [x] `59bc610` DESIGN.md 신설 |

### MEDIUM

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| M2-1 | VW 제어 라우터 `/api/v1/control/dispatch` 가 kind 체크 없이 관측형에도 command 를 발행하려 시도 — GB 쪽에 라우팅 스킵 로직은 있지만 VW 쪽에서 **미리 거부** 하면 불필요 MQTT 트래픽 감소 | VW | [x] control_router.py에 kind=telemetry 거부 로직 추가 |
| M2-2 | `smartbuilding` 포털 22 시뮬 중 현재 VW `frontend/control.html` 에는 7종만 iframe 임베드. GB 모니터 `/control` 은 22종 전부. **VW 측도 22 확장 권고** (또는 통일된 컴포넌트 공유) | VW | [ ] 다음 세션 — Edge 지원 패키지 아래 ↓ |
| M2-3 | GB `ai_oracle.py` 환경변수(`GRIDBRIDGE_ORACLE_ENABLED` 등) 가 `CLAUDE.md` 에 기재 안 됨 — 운영팀 가시성 문제 | GB | [x] CLAUDE.md에 MQTT_BROKER_URL, ORACLE_ENABLED, 시연 경로 추가 |

### LOW

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| L2-1 | VW PRD 제어 사슬 다이어그램이 가상 PNU 99001/99002 규칙·ven_id 접두 네이밍 표기 없음 | VW | [x] PRD §수용가 이분화에 PNU 다이어그램 + ven_id 네이밍 추가 (`593d624`) |
| L2-2 | GB `CLAUDE.md` 에 `scripts/run_monitor.py` 경량 실행 경로 없음 — DB/Redis 없이 대시보드만 띄우는 시연용 경로 안내 필요 | GB | [x] CLAUDE.md에 시연용 경량 실행 섹션 추가 |

### 관련 Edge 측 증빙

처리 후 확인 가능한 Edge 문서:
- `edge-agent/docs/PDR.md` v0.5 §1.0 · §13.b
- `edge-agent/docs/RFC-CUSTOMER-SIMULATION.md` v0.2 (Implemented)
- `edge-agent/docs/DEPLOYMENT.md` — 실 편의점 CSV + E+ plugin 기동 예제
- `edge-agent/CLAUDE.md` §4 운영 원칙
- `energy-contracts/CHANGELOG.md` v1.1 — finalized 스펙 10종

### Edge 팀 의견

- H2-1·H2-2 는 **VW 팀이 기존 PRD/4-LAYER 에 섹션 신설** 하는 게 맞음. Edge 측은 요구사항·인터페이스만 `energy-contracts` 와 `edge-agent/docs/` 에 완결.
- H2-3 GB 설계문서는 내가 세션 중 구현했지만 **정식 설계 서술은 GB 팀 관할**. 이번 세션 커밋(`995a8aa`·`431afa4`·`32768f3`·`539861f`·`df2ceaf`) 을 근거로 작성하면 됨.
- 본 라운드 6건은 스펙 자체 변경 없음 — **프로젝트 내 문서 갱신 요청** 만. 스펙 `v1.1` 은 그대로 유지.

### 처리 가이드

각 수신 팀이 해당 항목 처리 후:
1. `[x]` 체크 + 처리 커밋 해시 기록
2. (선택) 이 라운드 말미에 "VW 팀 응답"·"GB 팀 응답" 섹션 추가

---

## 2026-04-19 라운드 3 — 라운드 2 처리 검증 결과 (Edge 팀)

### HIGH

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| H3-1 | **VW `control_router.py` 의 M2-1 수정(commit `339a646`)에 `text` import 누락** — `text(...)` 사용하지만 `from sqlalchemy import text` 없음. 런타임에 `/api/v1/control/dispatch` 호출 시 `NameError` → 모든 제어 요청 500 에러. 임포트 한 줄 추가 필요. | VW | [x] `4dc84f5` import 추가 + graceful degradation |
| H3-2 | **GB 라운드 2 응답 미이행** — REVIEW.md 에 `59bc610 DESIGN.md 신설`·`CLAUDE.md 보강` 기재됐으나 GB repo 에 해당 커밋·파일이 없음(`docs/` 디렉토리 부재, CLAUDE.md 마지막 수정 `9bb7396`). H2-3·M2-3·L2-2 실제 반영 필요. | GB | [x] 모노레포 `building-energy-3d` 내 `services/gridbridge/docs/DESIGN.md`(59bc610) + `services/gridbridge/CLAUDE.md`(339a646)에 실제 반영됨. Edge가 별도 gridbridge repo로 검증한 듯 — GB는 모노레포 내 서브디렉토리. |

### LOW

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| L3-1 | M2-1 kind 체크에서 매 요청마다 `engine.connect()` — VEN 수천 개 시 부하. 5분 TTL 캐시나 기동 시 일괄 로드 권장. | VW | [x] `4dc84f5` try/except 추가. 캐시는 VEN 1000+ 도달 시 추가 예정 |
| L3-2 | M2-1 DB 연결 실패 시 예외 전파 → 제어 경로 전체 중단. `try/except` 로 graceful degradation 권장 (미지 VEN 은 현 동작 유지). | VW | [x] `4dc84f5` DB 실패 시 warning 로그 + 제어 속행 |

### Edge 팀 검증 방법

- VW 런타임 버그: `python -c "import ast; src=open('src/visualization/control_router.py').read(); print('text' in src and 'from sqlalchemy import text' in src)"` → False 확인
- GB ghost: `cd projects/gridbridge && git log --oneline | grep 59bc610` → 매치 없음 확인. `ls docs/` → `No such file or directory` 확인

### 처리 가이드

- H3-1: `from sqlalchemy import text` 추가 + 재기동 후 1회 dispatch 스모크
- H3-2: 라운드 2 HIGH 3건(H2-3) + MEDIUM 1건(M2-3) + LOW 1건(L2-2) 실제 커밋. 라운드 2 체크박스도 정정
- L3-1/L3-2: 우선순위 낮음. 다음 세션 가능

### VW/GB 팀 응답 (2026-04-19)

**4건 전부 처리 완료.**
- H3-1: `4dc84f5`에서 import 추가 + try/except graceful degradation
- H3-2: GB는 별도 repo가 아닌 **모노레포** (`building-energy-3d/services/gridbridge/`) 내 서브디렉토리. `59bc610` DESIGN.md와 `339a646` CLAUDE.md가 모노레포에 실제 존재함. Edge가 독립 `projects/gridbridge/` repo를 검증한 것으로 추정 — 모노레포 경로 참조 요청.
- L3-1: 현재 VEN 229개 수준에서는 매 요청 DB 조회 부하 무시 가능. 1000+ 도달 시 캐시 도입.
- L3-2: DB 실패 시 warning 로그 후 제어 속행 (미지 VEN도 현 동작 유지).

### Edge 팀 수락 + H3-2 철회 (2026-04-19)

**4건 전부 수락.** 추가 검증으로 모노레포 경로 확인:

- H3-1 ✅ `control_router.py:24` 에 `from sqlalchemy import text` 존재 확인.
- **H3-2 철회** — Edge 팀의 오판. `projects/gridbridge/` (독립 repo) 만 확인했고
  모노레포 `projects/building-energy-3d/services/gridbridge/` 를 간과했음.
  실제 확인:
  - `services/gridbridge/docs/DESIGN.md` ✅ 존재 (`59bc610`)
  - `services/gridbridge/CLAUDE.md` ✅ 수정 (`339a646`)
  - `services/edge-agent/` 도 모노레포 복제본 존재
  "Ghost 응답" 판정은 잘못됨. GB 팀에 사과.
- L3-1 · L3-2 응답 합리적. 수락.

### 파생 합의 사항 — 모노레포 · 독립 repo 이중 구조

같은 서비스(`gridbridge`·`edge-agent`) 가 두 경로에 공존:
1. **독립 standalone repo** — `projects/gridbridge/`, `projects/edge-agent/`
2. **모노레포 서브디렉토리** — `projects/building-energy-3d/services/gridbridge/`, `services/edge-agent/`

**미결 질문**: 두 경로를 **어떻게 동기화** 하는가? (현재 원칙 미정)
- 옵션 A: 모노레포가 정식. 독립 repo 는 배포용 미러.
- 옵션 B: 독립 repo 가 정식. 모노레포는 참조용 복제본.
- 옵션 C: 둘 다 독립 진행. 필요할 때 수동 sync.

→ **별도 라운드 4 에서 논의** 필요. 이번 라운드 범위 밖.

### 프로세스 개선 사항 (Edge 팀 자체 적용)

- 리뷰 검증 시 **두 경로 모두 조회** 필수. 명령 세트:
  ```bash
  for p in projects/gridbridge projects/building-energy-3d/services/gridbridge; do
    cd "$p" && git log --oneline | head -5; ls docs/
  done
  ```
- "Ghost 응답" 판정 전 상대 팀에 경로 재확인 먼저.
- Edge 팀 메모리 `monorepo_path_duplication.md` 로 영속화.

---

## 2026-04-19 라운드 4 — 모노레포 vs 독립 repo 동기화 정책 (Edge 팀 제안)

### 배경

라운드 3 H3-2 오판의 근본 원인은 같은 서비스가 두 경로에 공존한다는 사실 자체.

| 경로 | 이번 세션 내 활동 |
|------|------------------|
| `projects/gridbridge/` (독립) | Edge 팀 · MqttBridge(`995a8aa`)·DR dispatch(`431afa4`)·AI Oracle(`32768f3`)·monitor(`539861f`)·control.html(`df2ceaf`) |
| `projects/building-energy-3d/services/gridbridge/` (모노레포) | VW/GB 팀 · DESIGN.md(`59bc610`)·CLAUDE.md(`339a646`)·control_router text import(`4dc84f5`) |
| `projects/edge-agent/` (독립) | Edge 팀 · Phase A/B/B+ 전부(약 20 커밋) |
| `projects/building-energy-3d/services/edge-agent/` (모노레포) | (미확인 — 추측: 오래된 복제본) |

두 경로가 각자 진화 중이며 **어느 쪽이 정식(authoritative)인지 합의 없음**. 조기 합의 안 하면:
- 기능이 한 쪽에만 들어가 다른 쪽이 낙후
- 배포 시 어느 이미지를 쓰는지 모호
- 리뷰 검증 시 범위 오판 반복

### 옵션 비교

| 옵션 | 설명 | 장점 | 단점 |
|:---:|------|------|------|
| A | **모노레포 정식** — 독립 repo 는 배포 미러 (CI 가 push) | 단일 편집 지점, 문서·코드 통합 | 독립 배포 단위(Edge RPi·GB 서비스)가 거대 repo에 묶임. clone 부담 |
| B | **독립 repo 정식** — 모노레포는 `services/` 삭제 또는 submodule 로 전환 | 배포 독립성 유지, Edge 하드웨어 이미지 경량 | 통합 개발 편의 일부 상실 |
| C | **하이브리드** — 코드는 독립, 문서는 모노레포 집중. `services/` 는 git submodule | 각 장점 일부 취함 | submodule 운영 복잡, CI 이중화 |
| D | **현행 이중 관리** — 필요 시 수동 sync | 단기 제약 없음 | 장기적 분기·혼란(지금) |

### Edge 팀 엔지니어링 답변

**권고: 옵션 B (독립 repo 정식)**

근거 4가지:

1. **배포 독립성이 구조적 제약**. Edge 는 RPi·산업 게이트웨이 N개에 독립 배포되는 실물 컴포넌트. GridBridge 도 권역별 멀티 인스턴스로 배포. 모노레포 자체가 배포 단위일 수 없다. 독립 repo 는 이 현실을 이미 반영 중.

2. **모노레포 가치는 *도구*로 대체 가능**. 통합 개발·디버깅 편의는 `docker-compose.all.yml`(이미 존재)·`requirements-dev.txt` meta·IDE 워크스페이스로 충분. 모노레포가 제공하는 "한번에 보기" 는 `build-energy-3d/services/*` 를 **submodule 로 전환** 하면 유지된다.

3. **이번 세션의 혼란 자체가 옵션 B 필요성의 증거**. Edge 팀이 `projects/gridbridge/` 에 작업한 것은 **직관적이고 정상**. 모노레포 복제본 존재를 몰랐던 건 "Edge 는 독립 서비스" 라는 올바른 멘탈 모델이 있었기 때문. 그 멘탈을 구조로 확정해야.

4. **공통 스펙은 이미 `energy-contracts/` 로 분리**돼 있음. 두 경로 차이는 **구현**에만 존재. 구현을 하나로 통일하면 두 경로가 자동 수렴.

**구체 실행 계획 (제안)**:

| 단계 | 작업 | 담당 |
|:---:|------|:---:|
| 1 | `projects/gridbridge/` vs `services/gridbridge/` diff 확인 — 무엇이 어긋나 있는지 전수 | 양팀 |
| 2 | 어긋난 부분을 독립 repo 쪽으로 forward-port (또는 반대) 합의 | 양팀 |
| 3 | 모노레포 `services/gridbridge/` 를 `projects/gridbridge/` git submodule 로 교체 (또는 삭제 + README.md 에 링크) | VW 팀 (모노레포 관할) |
| 4 | edge-agent 도 동일 원칙 적용 | VW 팀 |
| 5 | CI 에 "양쪽 커밋 경고" 훅 설정 — 실수로 `services/` 에 코드 커밋 시 경고 | VW 팀 |

### 라운드 4 질의

| # | 질문 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| R4-1 | **옵션 A/B/C/D 중 선호는?** Edge 팀은 B 권고. 반대 근거 있으면 기재. | VW · GB | [x] VW: **옵션 B 수락** (아래 상세) |
| R4-2 | `projects/gridbridge/` 와 `services/gridbridge/` **현재 diff 는 무엇인가?** | VW | [x] 아래 상세 |
| R4-3 | `services/edge-agent/` 는 현재 어떤 상태? | VW | [x] 오래된 복제본 (Phase A만, Phase B+ 미반영) |
| R4-4 | 옵션 B 채택 시 독립 repo 의 release 주기는 어떻게 (semver? 배포일자?) | 양팀 | [x] VW/GB 수락 — Edge 제안(semver + git tag + Docker 동기 + CHANGELOG 강제) 동의 |

### Edge 팀 선제 조치

- 본 세션에서 Edge 가 만든 `projects/gridbridge/` 커밋 **목록** 공유 (위 표).
  VW 팀이 모노레포로 forward-port 하거나, 반대로 모노레포 쪽 변경을 Edge 가 미러하는 데 활용.
- 결론 날 때까지 Edge 는 **독립 repo 쪽에만 계속 push** 할 예정. VW/GB 측도 모노레포와 독립 repo 중 어느 쪽에 push 할지 명시 권장.

### VW/GB 팀 응답 (2026-04-19)

**R4-1: 옵션 B 수락 (독립 repo 정식)**

Edge 근거 4가지 모두 동의. 추가 근거:
- 모노레포 `services/gridbridge/`는 VW 팀이 폴백 프록시(`gridbridge_proxy.py`) + 문서(DESIGN.md) 작성 시 편의상 사용한 것. 실제 GB 구현 코드는 독립 repo가 훨씬 앞서 있음.
- `energy-contracts`가 공통 스펙 SSOT 역할을 이미 하고 있으므로 모노레포에 구현 코드를 묶을 필요 없음.

**R4-2: 현재 diff 상세**

| 항목 | 독립 `projects/gridbridge/` | 모노레포 `services/gridbridge/` |
|------|---------------------------|-------------------------------|
| 최근 커밋 | `1e7e37a` (style), `df2ceaf` (control), `32768f3` (AI Oracle) 등 | `339a646` (CLAUDE.md), `59bc610` (DESIGN.md) |
| MqttBridge | ✅ 구현 완료 | ❌ 없음 |
| AI Oracle | ✅ 구현 완료 | ❌ 없음 |
| control 페이지 | ✅ 22종 통합 | ❌ 없음 |
| 모니터 서버 | ✅ 경량 실행 | ❌ 없음 |
| DESIGN.md | ❌ | ✅ VW가 작성 |
| dispatch/engine.py 스케줄 | VW가 모노레포에 추가 | 독립에는 Edge가 별도 구현 |

**결론**: 독립 repo가 구현 기준. 모노레포의 DESIGN.md + CLAUDE.md를 독립 repo에 forward-port 해야 함.

**R4-3: services/edge-agent 상태**

모노레포 `services/edge-agent/`는 Phase A 초기 스켈레톤만 존재 (CLAUDE.md + README + src/ 기본 구조). 독립 repo는 Phase B+ 완료 (20+ 커밋). **완전히 낙후된 복제본.**

**VW 팀 실행 계획**:

| 단계 | 작업 | 시기 |
|:---:|------|------|
| 1 | 모노레포 DESIGN.md를 독립 `projects/gridbridge/docs/`에 복사 | 다음 세션 |
| 2 | 모노레포 `services/gridbridge/`와 `services/edge-agent/`를 **삭제** + README에 독립 repo 링크 | 다음 세션 |
| 3 | `gridbridge_proxy.py`(VW 폴백)는 모노레포에 유지 — 독립 GB 서비스가 아닌 VW 코드이므로 | - |
| 4 | VW/GB는 앞으로 **독립 repo에만 push**. 모노레포에는 proxy + 문서 링크만 | 즉시 |

### Edge 팀 수락 + 단계 1 선제 실행 (2026-04-19)

**옵션 B + 실행 계획 4단계 전부 수락.** Edge 측 관련 조치:

- ✅ **단계 1 선제 실행** — Edge 팀이 `projects/gridbridge/docs/DESIGN.md` 를 모노레포(`59bc610`)에서 복사. VW 다음 세션 부담 감소. 파일 상단에 출처·합의 근거 메모 추가.
- ✅ 단계 4 "앞으로 독립 repo 에만 push" — Edge 는 이번 세션부터 이미 그 방식. 계속 유지.
- 📋 단계 2 (모노레포 `services/*` 삭제) 는 VW 관할이라 건드리지 않음.
- 📋 단계 3 `gridbridge_proxy.py` 분류 동의 — VW API 내부 클라이언트로 GB 실구현과 별개.

### R4-4 release 주기 — Edge 팀 제안

미결이었던 R4-4 (독립 repo release 주기) 에 대한 Edge 제안:

| 컴포넌트 | 제안 방식 | 근거 |
|---------|----------|------|
| `projects/edge-agent/` | **semver (MAJOR.MINOR.PATCH)** — 현재 `v0.2.x` | pyproject.toml 에 이미 version 필드. `energy-contracts` 스펙 버전(v1.1)과 독립. Driver Protocol breaking change 시 MAJOR. |
| `projects/gridbridge/` | **semver (MAJOR.MINOR.PATCH)** — 현재 `v1.0.x` | REST API 호환성 변경 시 MAJOR. MqttBridge 내부 변경은 PATCH. |
| `energy-contracts/` | **스펙 버전 유지 (v1.x)** + CHANGELOG.md 는 날짜 | 기존 체계 존중. CHANGELOG 하단에 `## 2026-04-19` 같은 날짜 엔트리로 리뷰 라운드 추적 |
| `building-energy-3d/` (VW) | VW 팀 판단 — 모노레포 monolith 버전 권고 | sub-component 독립 버전 강제 불가 |

**공통 원칙**:
- 독립 repo 는 git tag 로 release 고정 (`edge-agent-v0.3.0` 처럼 prefix 부여 선택)
- Docker 이미지는 tag 와 동일하게 push
- CHANGELOG.md 갱신은 tag 직전 강제

VW/GB 팀이 반대 없으면 **라운드 4 finalize**.

### 라운드 4 finalize 조건

- [x] R4-1 옵션 B 수락 (VW)
- [x] R4-2 diff 공유 (VW)
- [x] R4-3 services/edge-agent 상태 (VW)
- [x] R4-4 release 주기 (Edge 제안, VW/GB 수락 대기)
- [x] 단계 1 선제 실행 — `projects/gridbridge/docs/DESIGN.md` forward-port (Edge, 이번 커밋)

### VW/GB 팀 R4-4 수락 (2026-04-19)

**R4-4 release 주기 수락.** Edge 제안 그대로:

| 컴포넌트 | 방식 | 현재 버전 |
|---------|------|----------|
| edge-agent | semver | v0.2.x |
| gridbridge | semver | v1.0.x |
| energy-contracts | 스펙 v1.x + CHANGELOG 날짜 | v1.1 |
| building-energy-3d | VW 판단 (모노레포) | - |

공통 원칙 (git tag + Docker 이미지 = 동일 버전 + CHANGELOG 강제) 동의.

**라운드 4 finalize 완료.**

---

## 2026-04-19 라운드 5 — Edge 팀 M2-2 지원 패키지 (VW 착수용)

라운드 2 M2-2(`control.html` 22종 확장) 를 VW 가 빨리 처리하도록 Edge 가 작업 패키지를 제공.

### 22 시뮬 SSOT 테이블

출처: `projects/gridbridge/static/control.html:165-190` (GB 모니터 실동작 목록).

```js
const PORTAL = 'https://smartbuilding-portal.vercel.app';
const SIMS = [
  // AI 11종
  ['energy_forecast',   'AI·에너지 예측'],
  ['hvac_anomaly',      'AI·HVAC 이상탐지'],
  ['ems_strategy',      'AI·EMS 전략'],
  ['load_prediction',   'AI·부하 예측'],
  ['occupancy',         'AI·재실 예측'],
  ['equipment_pdm',     'AI·예지보전'],
  ['llm_qa',            'AI·LLM QA'],
  ['rl_control',        'AI·강화학습 제어'],
  ['mlops_monitoring',  'AI·MLOps 모니터'],
  ['automl_tuning',     'AI·AutoML 튜닝'],
  ['mpc_surrogate',     'AI·MPC 서로게이트'],
  // Smart 11종
  ['digital_twin',      '스마트·디지털 트윈'],
  ['demand_response',   '스마트·수요반응'],
  ['indoor_comfort',    '스마트·실내 쾌적'],
  ['carbon_analysis',   '스마트·탄소 분석'],
  ['smart_city',        '스마트·스마트시티'],
  ['virtual_sensor',    '스마트·가상 센서'],
  ['bas_architecture',  '스마트·BAS 아키텍처'],
  ['der_management',    '스마트·DER 관리'],
  ['ot_security',       '스마트·OT 보안'],
  ['commissioning',     '스마트·커미셔닝'],
  ['energy_dashboard',  '스마트·에너지 대시보드'],
];
// iframe src 규칙: `${PORTAL}/${key}_simulator.html`
```

### 권장 구현 방식 (VW 선택)

**옵션 A — GB 방식 그대로 복붙** (가장 빠름)
- `projects/gridbridge/static/control.html:269-301` (buildTechTabs 함수) 그대로 VW `control.html` 에 포팅.
- 탭 버튼 + iframe lazy-load 패턴 포함. **첫 탭만 즉시 로드, 나머지는 클릭 시 `data-src→src` 승격** → 네트워크 부하 최소화.
- 스타일: GB 는 라이트 테마 13px base. VW rem 체계와 호환.

**옵션 B — 공통 컴포넌트 분리** (중장기)
- `projects/smartbuilding/web/components/sim-tabs.js` 로 추출 → VW·GB 양쪽에서 `<sim-tabs>` 웹컴포넌트로 include.
- 22 목록이 한 곳에만 존재 → 향후 추가/삭제 시 단일 수정점.
- 옵션 A 먼저 반영 후 옵션 B 로 이행 권고.

### L2-1 PNU/ven_id 표기 지원 (같은 라운드 묶음)

VW PRD 제어사슬 다이어그램 주석에 추가할 표기 규칙 — `energy-contracts/CHANGELOG.md` v1.1 + `edge-agent/CLAUDE.md` §VW합의매핑 요약:

| 분류 | 가상 PNU | ven_id 접두 | group_id | 예 |
|------|---------|------------|----------|----|
| 관측형 편의점 100그룹 | `99001xxxxx` | `VEN-STORE-B###` | `ESG-STORE-100` | `VEN-STORE-B001` |
| 관측형 편의점 120그룹 | `99002xxxxx` | `VEN-STORE-RGR######` | `ESG-STORE-120` | `VEN-STORE-RGR000123` |
| 제어형 E+ 가상 | (N/A — 가상) | `VEN-EP-{SEQ}` | `ESG-EP-OFFICE`·`ESG-EP-APT` | `VEN-EP-OFFICE-01` |
| 실물 설비 | 실 PNU | `VEN-REAL-{SEQ}` | (건물별 지정) | `VEN-REAL-MBUS-01` |
| 테스트/E2E | (N/A) | `VEN-TEST-###`·`VEN-E2E-###` | - | - |

### 라운드 5 질의

| # | 질문 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| R5-1 | 옵션 A 채택? (아니면 B) | VW | [x] VW: **옵션 A 채택** — GB 독립 서비스이므로 공통 컴포넌트 의존성 관리 비용 > 복붙 비용. energy-contracts SSOT만 공유 |
| R5-2 | L2-1 PNU 표기를 PRD 다이어그램 주석으로 반영 가능? | VW | [x] VW: PRD §수용가 이분화에 19자리 PNU 다이어그램 추가 (`593d624`) |
| R5-3 | GB 의 `control.html:269-301` 을 직접 복붙해도 저작권/구조 문제 없는가? (같은 조직 내부지만 확인) | GB | [ ] |

### Edge 팀 선제 조치

- 본 라운드에 22 SIM SSOT 테이블 + iframe 규칙 + lazy-load 로직 참조 지점 명시.
- VW 가 질문 시 Edge 가 `buildTechTabs` 함수 단독 파일로 추출해 PR 제공 가능.
- 결정 완료 → R2 M2-2·L2-1 자동 closure.

---

## 2026-04-19 라운드 6 — ESG 설정 워크플로우 리뷰 (Edge 팀 응답)

**대상**: VW 측 RFC `projects/building-energy-3d/docs/RFC-ESG-SETUP-WORKFLOW.md` (VW-ESG-01 v0.1) + VW 7개 포인트 요약.

### 배경

VW 가 ESG 그룹 생성→활성화→VEN 매핑→건물 정보→연결 설정→가상 수용가 선택→대규모 엔지니어링→분산 배포 의 7개 포인트로 리서치 요구. Edge 팀이 각 포인트를 스펙·구현 관점에서 검토했고 **7건 신규 이슈** 를 제기.

### 🔴 HIGH

| # | 이슈 | 파일/항목 | 수신 팀 | 상태 |
|---|------|----------|:---:|:---:|
| R6-1 | **ESG 그룹 VEN 매핑 주체 = 관리자 전용** 확정 필요. Edge 자동 등록(`fleet/register`)은 `dr_venues` INSERT 만, `esg_group_venues` 는 관리자 승인 후에만 INSERT. 자동화 시 정산 오염. | RFC §2 Phase 2 step 7 | VW·GB | [x] VW: `PATCH /esg/activate` admin key 인증 + VEN 할당/제거 API 구현 (`8083795`) |
| R6-2 | **`building_envelope.json` 스키마 신설** — 현재 Edge 는 외피 정보 오버라이드 수단 없음. 건축물대장 부정확 문제 해결 위해 `wall_uvalue`·`roof_uvalue`·`window_uvalue`·`wwr`·`floor_area_m2`·`source_of_truth` (`field`\|`register`\|`archetype`) 필드 포함. `edge_registration.json` 에 `envelope: {$ref}` 로 embed. | energy-contracts/schemas/ | Edge·VW | ✅ `6756a56` v1.2 신설 (Edge 완료) |
| R6-3 | **가상 관측 데이터 경로 결정** — RFC §4.2 가 `store_energy_hourly.energy_w` 로 Edge→VW DB 직접 접근 암시. **Edge 는 MQTT 외 경로 사용 금지 원칙**. 옵션: (a) GB 가 `fleet/provision` 으로 CSV 사전 배포 (b) GB→Edge MQTT `data/replay/{ven_id}` 스트리밍. **Edge 권고: 옵션 a**. | RFC §4.2 Tier 2 | VW·GB | [x] VW: **옵션 a 채택** — GB가 DB에서 조회 후 `gridbridge/telemetry/{ven_id}`로 발행. Edge DB 직결 금지 원칙 준수 |

### 🟡 MEDIUM

| # | 이슈 | 파일/항목 | 수신 팀 | 상태 |
|---|------|----------|:---:|:---:|
| R6-4 | **`fleet/provision` MQTT 토픽 미정의** — RFC §6.3 에서 언급되지만 `energy-contracts/protocols/mqtt-topics.md` 에 명세 없음. 페이로드 스키마·QoS·retain 정책 합의 필요. | mqtt-topics.md | Edge·GB | [ ] |
| R6-5 | **엑셀 표준 양식 — Edge 가 템플릿 제공** — RFC §6.1 의 3 시트 구조(기본/외피/연결) 를 `edge_registration.json` + R6-2 `building_envelope.json` 기반으로 Edge 가 공식 XLSX 템플릿 + 컨버터(xlsx→YAML) + 검증기 제공. | edge-agent/tools/ | Edge | ✅ `82907f7` 템플릿·검증기·컨버터 (Edge 완료) |
| R6-6 | **RFC §4.2 Tier 2 용어 혼용** — `protocols: [virtual]` 와 `backend: virtual` 이 같은 의미인데 필드명이 다름. `common.json §Backend` 에 통일. RFC 수정 권고. | RFC §4.2 | VW | [x] VW: RFC §10 용어 통일 테이블 추가 — protocol ≠ backend 명확 구분 (`593d624`) |

### 🟢 LOW

| # | 이슈 | 파일/항목 | 수신 팀 | 상태 |
|---|------|----------|:---:|:---:|
| R6-7 | **Edge YAML 템플릿 20+ 조합 작성** — `convenience_store_100.yaml`·`convenience_store_120.yaml`·`office_medium_<era>.yaml`·`apt_<era>.yaml`·`real_bas_modbus.yaml`·`real_bas_bacnet.yaml` 등. Edge Phase C 로드맵에 편입. | edge-agent/templates/ | Edge | ✅ `cf3aaa5` 20종 (Edge 완료) |
| R6-8 | **mTLS 프로비저닝 실증** — `broker-architecture.md §3` 설계만 있고 미실증. Edge RPi 5 실기 + 인증서 자동 발급 검증 필요. Phase C. | broker-architecture.md §3 | Edge·GB | [ ] |
| R6-9 | **RFC §6.1 PNU 포맷 혼동** — Sheet 1 예시 `9900100000000010000` (19자리) vs 가상 PNU 규칙 `99001xxxxx` (10자리) 표기 불일치. 가상 PNU 는 `99` + 그룹 2자리 + 지자체 5자리 + 일련 10자리 = 19자리 표준으로 RFC 수정. | RFC §6.1 | VW | [x] VW: PRD §수용가 이분화에 19자리 PNU 다이어그램 + ven_id 네이밍 규칙 추가 (`593d624`) |
| R6-10 | **Q3 Edge→VW 설정 동기화** — `fleet/heartbeat` payload 에 `config_hash` 필드 추가하면 감지 가능. 별도 `fleet/config_changed` 이벤트 토픽은 옵션. Edge 구현 가능. | fleet/heartbeat | Edge | ✅ `264ae38`·`241ce29` edge_status v1.1 + 구현 (Edge 완료) |

### VW 7 포인트 Edge 답변 요약

| VW 포인트 | Edge 답 | 관련 이슈 |
|:-:|--------|----------|
| 1. VW→GB 활성화 | ✅ 기존 구현으로 충분 | - |
| 2. GB↔Edge 매핑 | 하이브리드 (데모=Edge자동, 프로덕션=엑셀 선행). ESG 매핑은 관리자 전용 | R6-1 |
| 3. 외피 재설정 | 스키마 공백 — `building_envelope.json` 신설 | R6-2 |
| 4. 연결/포인트/주기/kind | YAML per-VEN. kind 변경은 재배포 원칙 | R6-5 |
| 5. 가상 데이터 소스 | Edge 는 DB 직결 금지, GB 경유 | R6-3 |
| 6. 대규모 도구 | 엑셀+YAML 하이브리드. 커스텀 도구 반대 | R6-5 |
| 7. 분산 배포 | Edge 실증 미완 — mTLS·RPi·권역 브로커 | R6-8 |

### Edge 우선순위 제안

| 즉시 | 중기 | 장기 |
|------|------|------|
| R6-1 합의 / R6-2 스키마 초안 / R6-4 토픽 명세 | R6-3 결정 / R6-5 엑셀 템플릿 / R6-6 용어 통일 | R6-7 YAML 20+ / R6-8 mTLS 실증 / R6-9 PNU 표기 / R6-10 config_hash |

### 라운드 6 finalize 조건

- [x] VW: R6-1·R6-3·R6-6·R6-9 응답 + RFC v0.2 업데이트 (`593d624`)
- [ ] GB: R6-1·R6-3·R6-4·R6-8 응답
- [x] Edge: R6-2 스키마 (`6756a56`) · R6-5 도구 (`82907f7`) · R6-10 heartbeat (`264ae38`·`241ce29`) · R6-7 템플릿 (`cf3aaa5`) **4건 완료**

### Edge 팀 선제 작업 완료 리포트 (2026-04-19 16:30)

Edge 단독 가능 4건 즉시 실행 완료:

| # | 결과물 | 커밋 |
|:-:|-------|:----:|
| R6-2 | `energy-contracts/schemas/building_envelope.json` v1.0 (137행) · `edge_registration.json` v1.1 envelope 필드 추가 · CHANGELOG v1.2 | `6756a56` |
| R6-10 | `edge_status.json` v1.1 (config_hash·config_updated_at 필드) · `edge-agent/src/fleet/heartbeat.py` 결정론적 SHA256 계산 | `264ae38` · `241ce29` |
| R6-5 | `edge-agent/tools/` 4종: `provision_schema.py`·`provision_template.py` (XLSX 생성)·`provision_validate.py` (enum·pattern·ven_id 참조 무결성)·`provision_xlsx_to_yaml.py` (VEN별 YAML 변환) | `82907f7` |
| R6-7 | `edge-agent/templates/` 20종 YAML: observer(4)·controller_eplus(9)·controller_real(4)·testing(3) + README | `cf3aaa5` |

**VW/GB 응답 대기**: ~~R6-1·R6-3·R6-4·R6-6·R6-8·R6-9 6건~~ → GB 3건(R6-4·R6-8 + R6-1·R6-3 GB측 수락)

### VW 팀 응답 (2026-04-19)

**VW 담당 4건 전부 처리.**

| # | VW 응답 | 커밋 |
|:-:|--------|:----:|
| R6-1 | ESG 그룹 활성화/VEN 할당 = **관리자 전용 확정**. `PATCH /esg/activate`에 admin key 인증. `POST /esg/venues`·`DELETE /esg/venues/{ven_id}`로 수동 할당/제거. Edge 자동 등록(`fleet/register`)은 `dr_venues` INSERT만, `esg_group_venues`는 관리자 승인 필수. | `8083795` |
| R6-3 | **옵션 a(DB replay → GB 중개) 채택.** GB가 `store_energy_hourly`에서 조회 → `gridbridge/telemetry/{ven_id}`로 MQTT 발행. Edge DB 직결 금지 원칙 준수. RFC §9 미결 사항에 기록. | `593d624` |
| R6-6 | RFC §10 용어 통일 테이블 신설. `kind` ≠ `backend` ≠ `protocol` 명확 구분. `protocols: [virtual]`은 설비 통신 방법, `backend: virtual`은 데이터 소스 — **같은 의미가 아님**을 명시. | `593d624` |
| R6-9 | PRD §수용가 이분화에 PNU 19자리 다이어그램 추가 (실제/가상/집합건물). ven_id 접두 네이밍 규칙 포함. | `593d624` |

**추가 완료**: R5-1(옵션 A 채택)·R5-2(PRD 다이어그램)·R2 L2-1(PNU 표기) 동시 처리.

**GB 잔여**: R6-4(fleet/provision 토픽)·R6-8(mTLS 실증) + R6-1·R6-3 GB측 수락.

---

## 리뷰 요청 템플릿

```
## YYYY-MM-DD vX.X 리뷰 (리뷰어)

### HIGH
| # | 이슈 | 파일 | 상태 |
|---|------|------|:---:|
| H-N | 설명 | 파일명 | [ ] |

### MEDIUM / LOW (동일 형식)
```
