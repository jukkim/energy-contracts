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
| M2-2 | `smartbuilding` 포털 22 시뮬 중 현재 VW `frontend/control.html` 에는 7종만 iframe 임베드. GB 모니터 `/control` 은 22종 전부. **VW 측도 22 확장 권고** (또는 통일된 컴포넌트 공유) | VW | [ ] 다음 세션 |
| M2-3 | GB `ai_oracle.py` 환경변수(`GRIDBRIDGE_ORACLE_ENABLED` 등) 가 `CLAUDE.md` 에 기재 안 됨 — 운영팀 가시성 문제 | GB | [x] CLAUDE.md에 MQTT_BROKER_URL, ORACLE_ENABLED, 시연 경로 추가 |

### LOW

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| L2-1 | VW PRD 제어 사슬 다이어그램이 가상 PNU 99001/99002 규칙·ven_id 접두 네이밍 표기 없음 | VW | [ ] 다음 세션 |
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
| H3-1 | **VW `control_router.py` 의 M2-1 수정(commit `339a646`)에 `text` import 누락** — `text(...)` 사용하지만 `from sqlalchemy import text` 없음. 런타임에 `/api/v1/control/dispatch` 호출 시 `NameError` → 모든 제어 요청 500 에러. 임포트 한 줄 추가 필요. | VW | [ ] |
| H3-2 | **GB 라운드 2 응답 미이행** — REVIEW.md 에 `59bc610 DESIGN.md 신설`·`CLAUDE.md 보강` 기재됐으나 GB repo 에 해당 커밋·파일이 없음(`docs/` 디렉토리 부재, CLAUDE.md 마지막 수정 `9bb7396`). H2-3·M2-3·L2-2 실제 반영 필요. | GB | [ ] |

### LOW

| # | 이슈 | 수신 팀 | 상태 |
|---|------|:---:|:---:|
| L3-1 | M2-1 kind 체크에서 매 요청마다 `engine.connect()` — VEN 수천 개 시 부하. 5분 TTL 캐시나 기동 시 일괄 로드 권장. | VW | [ ] |
| L3-2 | M2-1 DB 연결 실패 시 예외 전파 → 제어 경로 전체 중단. `try/except` 로 graceful degradation 권장 (미지 VEN 은 현 동작 유지). | VW | [ ] |

### Edge 팀 검증 방법

- VW 런타임 버그: `python -c "import ast; src=open('src/visualization/control_router.py').read(); print('text' in src and 'from sqlalchemy import text' in src)"` → False 확인
- GB ghost: `cd projects/gridbridge && git log --oneline | grep 59bc610` → 매치 없음 확인. `ls docs/` → `No such file or directory` 확인

### 처리 가이드

- H3-1: `from sqlalchemy import text` 추가 + 재기동 후 1회 dispatch 스모크
- H3-2: 라운드 2 HIGH 3건(H2-3) + MEDIUM 1건(M2-3) + LOW 1건(L2-2) 실제 커밋. 라운드 2 체크박스도 정정
- L3-1/L3-2: 우선순위 낮음. 다음 세션 가능

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
