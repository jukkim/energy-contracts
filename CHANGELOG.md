# Energy Contracts — CHANGELOG

스키마·프로토콜 버전 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

---

## v1.2 — 2026-04-19 (R6-2·R6-4·R6-10·R7-3)

### 개요
VW RFC-ESG-SETUP-WORKFLOW.md §5 "건축물대장 부정확" 문제 해결용 외피 스키마 신설 + 프로비저닝 채널 명세. 리뷰 라운드 6 대응. R7 응답 반영 (api_token_hash 추가).

### 신규 스키마
- `schemas/building_envelope.json` **v1.0** — 건물 외피·기하·설비 메타. `source_of_truth` (field/register/archetype) 우선순위, geometry(면적·층수·준공년도·방위·구조), envelope(U-value 4종·WWR·SHGC·VLT·기밀도), systems(HVAC·조명·기기부하·ESS·PV).
- `schemas/provision.json` **v1.0** — GB → Edge 프로비저닝 페이로드. provisioning_id(UUID) + revision(단조증가) + config(전체 Edge 설정) + apply_mode(hot_reload/restart_required/dry_run) + expected_config_hash.
- `schemas/provision_ack.json` **v1.0** — Edge → GB ack. applied/pending_restart/rejected/validated/hash_mismatch 상태 + actual_config_hash + reason + warnings.

### 갱신
- `edge_registration.json` — `envelope` 필드 추가 (building_envelope.json 참조).
- `edge_status.json` v1.2 — `config_hash` (16자리 hex) + `config_updated_at` + `api_token_hash` (R7-3, Edge 로컬 HTTP API 토큰 해시) 추가. VW 중앙 설정과 drift 감지 + 현장 토큰 드리프트 탐지.
- `protocols/mqtt-topics.md` — `fleet/provision/{ven_id}` (GB→Edge, QoS 2, Retain) + `fleet/provision_ack/{ven_id}` (Edge→GB) 추가. ACL 예시 갱신.

### 리뷰 연계
| 라운드 | 항목 | 해결 |
|:---:|------|:---:|
| R6 | R6-2 building_envelope.json 스키마 신설 | ✅ |
| R6 | R6-4 fleet/provision 토픽 + provision.json·provision_ack.json | ✅ (Edge 초안 — GB 수락 완료) |
| R6 | R6-10 edge_status.json config_hash | ✅ |
| R7 | R7-3 Edge 로컬 API 토큰 해시 heartbeat 포함 | ✅ (edge_status.json v1.2 api_token_hash) |

---

## v1.1 — 2026-04-19

### 개요
관측형(telemetry) vs 제어형(dispatch) 수용가 이분화. Edge 팀 스펙 4종 + 공용 enum SSOT 추가.

### 신규 스키마
- `schemas/venue.json` **v1.1** — 수용가 레지스트리. `kind × backend` 이원 분류.
- `schemas/virtual_prosumer.json` **v1.0** — E+ 가상 수용가 I/O 계약 (observable·controllable·step_seconds·real_time_factor).
- `schemas/control_response.json` **v1.0** — 제어 명령 적용 결과 (requested vs actual, interlocks).
- `schemas/edge_registration.json` **v1.1** — Edge 자동 등록 메타 (edge_type·location·ep_model·capabilities).
- `schemas/edge_status.json` **v1.0** — heartbeat + 드라이버별 연결 상태 + 큐 사이즈.
- `schemas/common.json` **v1.0** — 공용 enum·패턴 SSOT (Strategy·Kind·Backend·BuildingType·EdgeType·SignalLevel·VenId·VirtualPNU).

### 기존 스키마 갱신 (description 보강만, 호환성 유지)
- `control_command.json` — strategy description에 "common.json §Strategy SSOT 동기화" 명시. constraints 각 필드에 기본값 서술.
- `control_response.json` — strategy description에 "status=failed/rejected 시 생략 가능" 명시.
- `dr_event.json` — end_time description에 "CANCELLED 시 원래 예정 종료 시각 보존" 명시.

### 프로토콜
- `protocols/mqtt-topics.md` — Edge→GB 방향(control_response·registration·heartbeat) + fleet/register·fleet/heartbeat·fleet/{ven}/ota 토픽, ven_id 네이밍 정규식(5 접두), mosquitto ACL 예시(14 토픽), kind 라우팅 규칙.
- `protocols/broker-architecture.md` — VW 측 제안(Mosquitto/EMQX 단계·인증·Edge 3유형·ESG 그룹 4종·역할 분담). §9 TODO 7건 중 4건 완료 체크, 3건 Edge 제안 반영.

### 수용가 이분화 (CLAUDE.md)
- 관측형(`kind=telemetry`) — 편의점 220채 DB replay. `command/schedule` 발행 스킵.
- 제어형(`kind=dispatch`) — E+ 가상·실 BAS. 양방향.
- ESG 사전 정의 그룹 4종: `ESG-STORE-100`(100채), `ESG-STORE-120`(124채), `ESG-EP-OFFICE`, `ESG-EP-APT`.
- 가상 PNU: `99001xxxxx`=100그룹, `99002xxxxx`=120그룹.
- ven_id 접두: `VEN-STORE-·VEN-EP-·VEN-REAL-·VEN-TEST-·VEN-E2E-`.

### 리뷰 라운드
| 날짜 | 커밋 | 내용 |
|------|:---:|------|
| 2026-04-19 | `a60efee` | Edge측 스펙 4종 + 관측형/제어형 이분화 (v1.1 초안) |
| 2026-04-19 | `4db7f9a` | VW broker-architecture §5 예시·§3 ACL 정합 교정 + §9 TODO 응답 |
| 2026-04-19 | (이 커밋) | REVIEW.md HIGH 1 + MEDIUM 3 + LOW 2 반영 (common.json 신설, description 보강, CHANGELOG 신설) |

### 버전 동시 변경 관계

`edge_registration.json` v1.1 과 `venue.json` v1.1 은 동일 동기 — 수용가 분류체계(`kind`·`backend`)가 양쪽 모두에 나타나며 공용 SSOT(`common.json`)를 참조한다. 둘 중 하나만 bump 되는 변경은 금지.

---

## v1.0 — 2026-04-19

초기 릴리즈.

### 스키마
- `dr_event.json` — DR 이벤트 (GB 생성)
- `reduction_schedule.json` — 감축 스케줄 (VW/GB → Edge)
- `control_command.json` — 제어 명령 (VW/GB → Edge)
- `telemetry.json` — 텔레메트리 (Edge → GB/VW)

### 프로토콜
- `protocols/mqtt-topics.md` 초안
- 경로 0~4 정의 (사용자→VW, VW→GB→EA, VW→EA, EA→VW, EA→GB→VW)
