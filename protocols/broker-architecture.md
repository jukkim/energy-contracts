# MQTT 브로커 아키텍처

> 최종 수정: 2026-04-19  
> 상태: 초안 (VWorld 측 제안 → Edge 팀 리뷰 필요)

## 1. 개요

```
Edge₁ (RPi/가상) ─┐
Edge₂             ─┤
  ...              ├─→ MQTT Broker ─→ GB Worker(s) ─→ PostgreSQL
Edge_n (EP 에뮬) ─┤                ─→ VWorld (직접 구독)
가상Edge 224점포 ──┘
```

**원칙**: Edge는 브로커 주소만 알면 된다. GB/VWorld 주소를 알 필요 없다.

## 2. 브로커 선택

| 옵션 | 라이선스 | 동시접속 | 추천 단계 |
|------|---------|---------|----------|
| **Mosquitto** (Docker) | EPL-2.0 (무료) | ~10K | PoC / 파일럿 |
| **EMQX** (Docker) | Apache-2.0 (무료) | ~100K+ | 파일럿 / 프로덕션 |
| AWS IoT Core | 종량제 | 무제한 | 프로덕션 (비용 발생) |

**PoC 단계 권장**: Mosquitto Docker 컨테이너 1개.

```yaml
# docker-compose.yml 추가
mqtt:
  image: eclipse-mosquitto:2
  ports:
    - "1883:1883"    # MQTT
    - "9001:9001"    # WebSocket (프론트 대시보드용)
  volumes:
    - ./config/mosquitto.conf:/mosquitto/config/mosquitto.conf
    - mqtt_data:/mosquitto/data
  restart: unless-stopped
```

## 3. 인증 / 보안

| 단계 | 인증 방식 | 비고 |
|------|----------|------|
| PoC | username/password (mosquitto passwd) | Edge별 개별 계정 |
| 파일럿 | TLS + client certificate | Edge 인증서 사전 발급 |
| 프로덕션 | mTLS + ACL | 토픽별 읽기/쓰기 권한 분리 |

**ACL 예시** (Edge는 자기 ven_id 토픽만 접근 — 완전판은 `mqtt-topics.md §ACL`):
```
user VEN-STORE-001
topic write gridbridge/telemetry/VEN-STORE-001
topic write gridbridge/ack/VEN-STORE-001
topic write gridbridge/alert/VEN-STORE-001
topic write gridbridge/control_response/VEN-STORE-001
topic write vworld/telemetry/VEN-STORE-001
topic write vworld/alert/VEN-STORE-001
topic write fleet/register/VEN-STORE-001
topic write fleet/heartbeat/VEN-STORE-001
topic read  gridbridge/command/VEN-STORE-001
topic read  gridbridge/schedule/VEN-STORE-001
topic read  fleet/VEN-STORE-001/ota
topic read  external/smp
topic read  external/temp/VEN-STORE-001
```

## 4. Edge 유형

| 유형 | 설명 | 데이터 소스 | 제어 가능 |
|------|------|-----------|----------|
| **실물 Edge** | RPi 5 + BACnet/Modbus 센서 | 실시간 설비 계측 | O (릴레이/BMS) |
| **가상 Edge (편의점)** | Python 스크립트, DB replay | store_energy_hourly | X (읽기 전용) |
| **가상 수용가 (EP)** | EnergyPlus 에뮬레이션 | 시뮬레이션 결과 | O (EMS 전략 M0~M8) |

### 가상 수용가 (EnergyPlus 에뮬레이션)

> **이 섹션은 Edge 팀이 구체화해야 합니다.**

```
제어 명령 (GB→Edge)          EnergyPlus 에뮬레이터           응답 (Edge→GB)
───────────────────     ─────────────────────────     ──────────────────
control_command.json  →  IDF 수정 → EP 실행 → 결과  →  control_response.json
  strategy: "M5"          (EMS actuator 조정)           reduction_kw: 45.2
  reduction_kw: 50        (1시간 시뮬 실행)              actual_temp: 26.3
```

**Edge 팀에 요청하는 사항**:
1. EP 에뮬레이터의 **입력 인터페이스** (어떤 제어 파라미터를 받는지)
2. EP 에뮬레이터의 **출력 인터페이스** (어떤 결과를 반환하는지)
3. **응답 시간** (실시간? 배치? 시뮬 1시간에 실제 몇 초?)
4. **건물 유형별 IDF** (어떤 건물을 에뮬레이션하는지)

→ 합의된 인터페이스를 `schemas/virtual_prosumer.json`과 `schemas/control_response.json`에 기록.

## 5. Edge 등록 흐름

```
1. Edge 시작 → fleet/register publish
2. GB Worker 수신 → dr_venues INSERT (is_active=FALSE)
3. 관리자 승인 → is_active=TRUE
4. Edge → 정상 telemetry 송신 시작
```

**등록 페이로드** (`schemas/edge_registration.json` v1.1 기준):
```json
{
  "ven_id": "VEN-EP-OFFICE-001",
  "edge_type": "energyplus_emulator",
  "kind": "dispatch",
  "backend": "energyplus",
  "building_type": "office_medium",
  "group_id": "ESG-EP-OFFICE",
  "location": {"lat": 37.566, "lng": 126.978},
  "pnu": "9900000000010000",
  "ep_model": "medium_office_2010_RC",
  "baseline_kw": 500,
  "max_reduction_kw": 200,
  "capabilities": {
    "supported_strategies": ["M0", "M3", "M5", "M7"],
    "controllable_points": ["hvac_setpoint", "lighting_pct", "ess_discharge"],
    "has_ess": true,
    "has_pv": false,
    "step_seconds": 600
  },
  "software": {
    "firmware_version": "1.0.0",
    "edge_agent_version": "0.2.0",
    "driver_types": ["energyplus"]
  },
  "registered_at": "2026-04-19T12:00:00+09:00"
}
```

## 6. 가상 ESG 그룹

| 그룹 ID | 이름 | Edge 유형 | 수량 | 용도 |
|---------|------|----------|------|------|
| ESG-STORE-100 | 편의점 100 (에너지) | 가상 Edge (DB replay) | 100 | ESG 에너지 분석 |
| ESG-STORE-120 | 편의점 120 (센서) | 가상 Edge (DB replay) | 120 | ESG + 센서 분석 |
| ESG-EP-OFFICE | EP 가상 오피스 | 가상 수용가 (EP) | TBD | 제어 검증 |
| ESG-EP-APT | EP 가상 아파트 | 가상 수용가 (EP) | TBD | 제어 검증 |

## 7. 양쪽 역할 분담

| 항목 | VWorld/GB 측 | Edge 측 |
|------|-------------|---------|
| 브로커 운영 | Docker 배포 + 모니터링 | - |
| 토픽 설계 | GB→Edge 방향 | Edge→GB 방향 보강 |
| 제어 명령 스펙 | control_command.json 유지 | control_response.json **신규 작성** |
| 가상 수용가 | - | virtual_prosumer.json **신규 작성** |
| Edge 등록 | dr_venues 자동 INSERT | edge_registration.json **신규 작성** |
| 텔레메트리 | telemetry.json 유지 | 필드 추가 시 PR |
| ESG 그룹 매핑 | esg_groups + esg_group_venues | Edge가 ven_id 할당 규칙 준수 |

## 8. 기존 스키마 현황

아래 스키마는 이미 정의 완료:

| 스키마 | 상태 | 설명 |
|--------|------|------|
| `schemas/edge_registration.json` | **완료** | kind, backend, capabilities, hardware/software |
| `schemas/virtual_prosumer.json` | **완료** | observable/controllable 포인트, step_seconds, real_time_factor |
| `schemas/control_response.json` | **완료** | status(applied/clamped/rejected), interlocks, reduction_kw |
| `schemas/control_command.json` | **완료** | M0~M8 전략, 제어 파라미터 |
| `schemas/telemetry.json` | **완료** | Edge→GB 계측 데이터 |
| `schemas/edge_status.json` | **완료** | heartbeat + 상태 |

## 9. TODO (양쪽 합의 필요) — Edge 팀 응답 추가

- [x] `protocols/mqtt-topics.md`에 `fleet/register`, `fleet/{ven_id}/ota` 토픽 추가 — **반영됨 (commit a60efee)**
- [x] ESG 그룹 ID 네이밍 규칙 확정 — **CLAUDE.md §ESG 사전 정의 그룹에 4개 고정**: `ESG-STORE-100` · `ESG-STORE-120` · `ESG-EP-OFFICE` · `ESG-EP-APT`
- [x] ven_id 네이밍 규칙 확정 — **mqtt-topics.md §ven_id 네이밍 규칙 + edge_registration.json pattern에 반영**. 접두 5종(`VEN-STORE-`/`VEN-EP-`/`VEN-REAL-`/`VEN-TEST-`/`VEN-E2E-`), 접두 뒤는 영숫자·하이픈 자유.
- [x] mqtt-topics.md에 본 문서의 토픽 설계 통합 — **반영됨**
- [ ] **가상 PNU 네이밍 규칙** — Edge 팀 제안: 시도코드 `99`(가상) + 시군구 `99`(임의) + 순번. 예 `9999000000010000`(E+ 가상 오피스) / `9999100000000001`(편의점 가상 1번). 최종 결정은 VW 팀.
- [ ] **EP 에뮬레이터 real_time_factor 운영 값** — Edge 팀 제안: PoC `60x`(1분→1초, 1시간 시뮬≈1분 벽시계), 파일럿 `1x`(실시간), 검증용 `300x`(1시간≈12초). `virtual_prosumer.json.real_time_factor`로 VEN별 설정 가능.
- [ ] **브로커 인증 방식 PoC** — Edge 팀 제안: `username/password` + ACL 파일(위 예시). mosquitto-go-auth 플러그인은 파일럿으로 지연. mTLS는 프로덕션. `MQTT_USER`·`MQTT_PASS` 환경변수로 Edge에 주입.

## 10. 스펙 정합성 체크 (Edge 팀 리뷰 결과)

2026-04-19 리뷰 라운드:

- ✅ 모든 schemas/*.json 이 JSON Schema Draft 2020-12로 파싱됨
- ✅ examples/ 3개 페이로드 모두 대응 스키마 validate 통과
- ✅ §5 등록 페이로드 예시가 `edge_registration.json` v1.1에 통과 (kind, backend, registered_at, capabilities.object 반영)
- ✅ §3 ACL 예시가 `mqtt-topics.md` §ACL 과 동일 토픽 집합으로 정렬
- ✅ ven_id 네이밍 정규식 smoke test 7건 통과
