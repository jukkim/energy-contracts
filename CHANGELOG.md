# Energy Contracts — CHANGELOG

스키마·프로토콜 버전 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

---

## 0.2.0 — 2026-05-27 critics 패키지 신설 (SSOT_GOVERNANCE §9 도메인 횡단 분리)

### 신규
- `energy_contracts/critics/` — 4 종 Critic + CriticsGate 조합자 (도메인 중립 SSOT)
  - `critic_base.py` — Critic ABC + CriticResult + Verdict (PASS/WARN/FAIL)
  - `c_legal.py`    — 법령 인용 정확성 (`rules/legal-citation.md`)
  - `c_carbon.py`   — 배출계수 SSOT 정합 (`CARBON_EMISSION_FACTORS.yaml`)
  - `c_safety.py`   — HVAC/PMV/ESS/조명 interlock
  - `c_data.py`     — NDA 출처 fingerprint (`rules/private-data-disclosure.md`, zero-tolerance)
  - `gate.py`       — CriticsGate (실시간 3 종 + 사후 batch debate 4 종) + summarize_dispatch_for_critics
- `tests/test_critics.py` — 5 test (clean 90% 통과 + violation 80% 검출 + zero-tolerance + serialize)
- `tests/test_critics_gate.py` — 13 test (summary builder + realtime gate + cache + batch debate)
- `__version__` 0.1.0 → 0.2.0, `pyproject.toml` 동일

### 이동 (be-3d → EC)
- `building-energy-3d/src/critics/` → `energy_contracts/critics/` (5 파일)
- `building-energy-3d/src/agents/dr/critics_gate.py` → `energy_contracts/critics/gate.py`
- `building-energy-3d/tests/test_critics.py` → `tests/test_critics.py`
- `building-energy-3d/tests/unit/dr/test_critics_gate.py` → `tests/test_critics_gate.py`

### SSOT 거버넌스
- `myjob/docs/SSOT_GOVERNANCE.md` §9 신규 — 도메인 횡단 로직 분리 원칙 (3 계층 책임 분리 + Q1~Q4 진입 판정 + DR Critics 사례)
- 영향 repo (lockstep release): be-3d (import 마이그), gridbridge (신규 realtime owner wire-up)

### 회귀
- EC critics tests 18/18 PASS

---

## (unversioned) — 2026-05-25 security_policy.json v1.1 (CSP 강화, P6 SSOT cascade)

### 변경
- `security_policy.json` `default.headers.Content-Security-Policy`:
  - `script-src` 에서 `'unsafe-eval'` 제거
  - `style-src` 에서 `'unsafe-inline'` 제거
- `version` 1.0 → 1.1, `updated` 2026-05-25
- be-3d CSP P5 #A~#D 완료 (2026-05-25, be-3d `bb72f51`) 반영
- Cesium 의존 페이지(`vworld.html`/`cesium.html`) 와 legacy simulator iframe(`/simulators/*`)은 be-3d nginx location 에서 개별 완화 — SSOT default 와 별개

### 영향
- 6 consumer `_generated_constants.{py,ts}` cascade — `gen_constants.py --all` 실행, drift 0 확인
  - `building-energy-3d/src/shared/_generated_constants.py`
  - `building-energy-3d/frontend/src/shared/_generated_constants.ts` (security 미포함 — exports 화이트리스트)
  - `gridbridge/src/_generated_constants.py`
  - `edge-agent/src/_generated_constants.py`
  - `agentleague/backend/_generated_constants.py`
  - `eduarena/backend/_generated_constants.py`
- be-3d FastAPI `SecurityHeadersMiddleware` + gridbridge `main.py` + agentleague `main.py` 가 SSOT 직접 import — 재빌드/재시작 시 신규 CSP 자동 적용 (API JSON 응답에만 영향, nginx 가 서빙하는 HTML 은 nginx CSP 사용)
- 회귀: gridbridge 290 PASS, be-3d SSOT consistency 26 PASS (1 pre-existing path bug 무관)

---

## 0.1.0 — 2026-05-19 패키지화 + wheel 배포 (Phase C, agents a12)

### 추가
- `pyproject.toml` — setuptools 기반 패키지 정의 (`requires-python = ">=3.11"`)
- `energy_contracts/__init__.py` — `load_schema()`, `list_schemas()`, `SCHEMAS_DIR` 헬퍼
- `energy_contracts/_pydantic_models/__init__.py` — 서브패키지 진입점
- wheel: `dist/energy_contracts-0.1.0-py3-none-any.whl` (52 schemas + 2 models + dist-info, 59 files)

### 이동 (R, 57 파일)
- `schemas/*.json` → `energy_contracts/schemas/*.json` — wheel package data 로 포함
- `scripts/_pydantic_models/*.py` → `energy_contracts/_pydantic_models/*.py`

### 도구 path 갱신 (`SCHEMAS_DIR`)
- `scripts/gen_constants.py:30` — `CONTRACTS_ROOT / "energy_contracts" / "schemas"`
- `scripts/validate_ssot.py:33` — 동일
- `scripts/gen_pydantic_models.py:19-20` — `SCHEMAS_DIR` + `OUT_DIR` 모두 `energy_contracts/` 하위
- `scripts/classify_tests.py:31` — `test_classification.json` 경로 갱신

### 호환성
- 5 consumer repo `_generated_constants.{py,ts}` SOURCE_HASH 동기화 유지 (드리프트 없음, `validate_ssot.py` 통과)
- 기존 `python energy-contracts/scripts/gen_constants.py --all` 진입점 그대로 (내부 path 만 변경)
- agents repo 가 `pip install -e ../energy-contracts` 또는 wheel 로 import 검증 ✅ (agents `.venv` Py 3.11.9 + be-3d `venv` Py 3.13.3 모두 통과)

---

## (unversioned) — 2026-05-18 H11 cross-platform hash fix + TD-9 단위 테스트

### gen_constants.py 버그 수정
- `schemas_hash()` 가 `read_bytes()` 로 self-bytes 를 읽어 Windows(CRLF) / Linux(LF) 에서 hash 가 달랐음 → CI 서버측 검증에서 false-positive DRIFT 발생
- Fix: `read_text(encoding="utf-8").encode("utf-8")` 로 newline 정규화 (PR #2, `be3c75b`)
- SOURCE_HASH cascade: `58ff101d` → `1a793963` (5 consumer repo 6 파일 regen)

### 신규 단위 테스트 (TD-9, PR #3)
- `tests/test_classify_tests.py` — `_strip_headerless_pytestmark` 4 케이스 (canonical_only / raw_only / **H1 회귀 canonical+raw** / dangling import)
- pytest 4/4 PASS (0.23s)

### 서버측 SSOT pre-merge gate (H11)
- 5 consumer repo (edge-agent / gridbridge / agentleague / eduarena / building-energy-3d) 에 `.github/workflows/ssot-drift.yml` 추가
- PR/push 시 energy-contracts master 와 `_generated_constants.*` drift 자동 검출 (서버측 강제, `--no-verify` 우회 차단)
- grep 필터로 자기 repo 외 sibling MISSING 무시

---

## v1.4.0 — 2026-04-23 (R16/R17 + VW forecast/anomaly + GB bulk sync)

### 개요
VW 에너지 예측(PatchTST 168→24h) + 이상탐지 API 및 GB ESG VEN 일괄 동기화 스키마 추가.
R16 Phase A 완료(5 VEN 실측 검증), R17 Item 1~5 RESOLVED.

### 신규 스키마
- `schemas/forecast_response.json` — PatchTST 168h→24h 예측 응답 (entity_id, model, forecast[24], metrics)
- `schemas/anomaly_response.json` — 이상탐지 응답 (z_score/isolation_forest/forecast_residual, status, score 0~1)
- `schemas/esg_venue_bulk_sync.json` — PUT /esg/groups/{id}/venues 요청·응답 (R14-8 BulkVenueSync)

### 리뷰 라운드 상태 갱신
- R16: Phase A 완료 (5 VEN × 실측 데이터 MQTT 적재 검증) · Phase B(168→24 예측), Phase C(이상탐지) 대기
- R17: Item 1~5 RESOLVED · Item 6(UI regression) ACK(중기)

---

## (unversioned) — 2026-04-21 라운드 9 Edge 응답

Edge 팀이 VW/GB 의 Tailscale 경로 제안(라운드 9) 에 일괄 답변. 스키마 변경 없음, REVIEW.md 만 갱신.

- R9-1 Tailscale 옵션 A **수락**
- R9-2 PoC 는 공용 Tailscale, 정식 운영은 Headscale (self-hosted) 선호
- R9-3 Docker `0.0.0.0:1883` + iptables (`tailscale0` only) 2중 방어
- R9-4 **R6-8 mTLS Phase D 강등 제안** — Tailscale 이 전송 암호화 + peer 인증 제공, ACL 은 Tailscale tag 로 대체
- R9-5 RPi 5 Tailscale 추정 30~50 MB · CPU <2% — `bench_rpi5.py` 에서 실측 예정
- 실행 단계 4 (RPi 5 Tailscale 설치) — Edge 담당 · RPi 5 실기 확보 대기

---

## v1.3.1 — 2026-04-20 (ARCH-R8-1 AUDIT-R2)

### 개요
Edge 감사 P1 반영. Edge·GB·VW 3계층에서 `commissioning_hash` 알고리즘이 드리프트할 위험 차단.

### 신규 프로토콜 문서
- `protocols/commissioning-hash.md` — `commissioning_hash` 알고리즘 SSOT. canonical JSON(`sort_keys=True, separators=(",",":"), ensure_ascii=False`) + UTF-8 + SHA-256. Edge/GB/VW 구현 모두 이 문서 참조 필수.

### 스키마 갱신
- `schemas/engineering_session.json` — `commissioning_hash.description` 에 알고리즘 SSOT 링크 명시.

---

## v1.3 — 2026-04-20 (R8-5)

### 개요
Edge Engineering/Monitoring 분리 + 22기술 번들·세션 저장. 라운드 8 VW/GB 합의 후 Edge 팀이 작성한 3 스키마 초안 + MQTT 토픽 2종. GB Tech Catalog Registry + Bundle Builder 구현 대기 (R8-2, 4주 공수).

### 신규 스키마
- `schemas/engineering_session.json` **v1.0** — 기사 설치 세션 (session_id, technician_id, selected_techs, provisioning_config $ref provision.json#/config, dry_run_result, commissioning_hash, previous_session_id). Edge seal 시 로컬 `sessions/*.yaml` + `fleet/engineering/{ven_id}` retain 발행.
- `schemas/engineering_diff.json` **v1.0** — 세션 간 변경 체인. techs_added/removed + config_changes (JSON Pointer 기반) + bundle_version_change. Edge `fleet/engineering_diff/{ven_id}` 발행, GB append-only 이력 저장.
- `schemas/bundle_manifest.json` **v1.0** — 22기술 번들 루트 manifest. version(semver), min_edge_schema, tech_list[](id, sha256, supported_backends, applicable_building_types), signature (ed25519). Edge A/B atomic swap + 서명 검증.

### 프로토콜 갱신
- `protocols/mqtt-topics.md`:
  - `fleet/engineering/{ven_id}` — Edge pub (QoS 1, retain=True) · GB+VW sub
  - `fleet/engineering_diff/{ven_id}` — Edge pub (QoS 1, retain=False) · GB+VW sub
  - ACL 예시 갱신 + mTLS Phase C cert subject 정책 명시

### VW/GB 합의 (라운드 8, `5d596d5`)
- Engineering/Monitoring 분리 + 3역할 권한 (R8-1)
- GB Tech Catalog Registry + Bundle Builder 4주 착수 (R8-2)
- 서명 키 GB 위탁, Edge 공개키 embed (R8-8)
- mTLS Phase C RPi 5 완료 후 (R8-9)
- Fleet 히트맵 VW 포털 관리자 탭 (R8-10)

### 참조
- Edge 설계: `edge-agent/docs/DESIGN-EDGE-ENGINEERING.md`
- Edge 로드맵: `edge-agent/docs/ROADMAP-R8.md`
- 감사: `edge-agent/docs/AUDIT-2026-04-20.md`

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
