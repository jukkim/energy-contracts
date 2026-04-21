# MQTT 토픽 규칙

## 네이밍 컨벤션

```
{root}/{kind}/{identifier}
```

- `root`: `gridbridge` (GB가 허브인 채널) · `vworld` (VW 직접 피드백) · `external` (외부 신호)
- `kind`: command · schedule · telemetry · ack · alert · status · registration · heartbeat · control_response
- `identifier`: `{ven_id}` 또는 `{group_id}`

## 토픽 목록

### GB → Edge (제어형 수용가에만 발행)

| 토픽 | 발행자 | 구독자 | QoS | Retain | 스키마 |
|------|:---:|:---:|:---:|:---:|------|
| `gridbridge/command/{ven_id}` | GridBridge · VWorld | EdgeAgent | 2 | Yes | `control_command.json` |
| `gridbridge/schedule/{ven_id}` | GridBridge · VWorld | EdgeAgent | 2 | Yes | `reduction_schedule.json` |

> **관측형(telemetry) 수용가**는 구독만 하거나 kind=telemetry로 등록된 경우 이 토픽으로 아무것도 발행되지 않는다(GB의 kind 라우팅 규칙).

### Edge → GB / VW (모든 kind 공통)

| 토픽 | 발행자 | 구독자 | QoS | Retain | 스키마 |
|------|:---:|:---:|:---:|:---:|------|
| `gridbridge/telemetry/{ven_id}` | EdgeAgent | GridBridge | 1 | No | `telemetry.json` |
| `vworld/telemetry/{ven_id}` | EdgeAgent | VWorld | 1 | No | `telemetry.json` (경로3 미러) |
| `gridbridge/ack/{ven_id}` | EdgeAgent | GridBridge | 1 | No | `control_response.json` (부분) |
| `gridbridge/control_response/{ven_id}` | EdgeAgent | GridBridge · VWorld | 1 | No | `control_response.json` |
| `gridbridge/alert/{ven_id}` | EdgeAgent | GridBridge | 2 | No | (alert payload) |
| `vworld/alert/{ven_id}` | EdgeAgent | VWorld | 2 | No | (alert payload) |
| `fleet/register/{ven_id}` | EdgeAgent | GridBridge | 2 | Yes | `edge_registration.json` (VW broker-architecture §5) |
| `fleet/heartbeat/{ven_id}` | EdgeAgent | GridBridge | 1 | Yes | `edge_status.json` |
| `fleet/{ven_id}/ota` | GridBridge | EdgeAgent | 1 | Yes | OTA 업데이트 지시 (미래) |
| `fleet/provision/{ven_id}` | GridBridge | EdgeAgent | 2 | Yes | `provision.json` (R6-4) — VW 엑셀/UI 편집 결과 배포. apply_mode 지정. R6-3 옵션 a 관측 데이터 배포도 이 토픽 사용 |
| `fleet/provision_ack/{ven_id}` | EdgeAgent | GridBridge | 1 | No | `provision_ack.json` — provisioning_id 로 매칭. applied/pending_restart/rejected/validated/hash_mismatch |
| `fleet/engineering/{ven_id}` | EdgeAgent | GridBridge · VWorld | 1 | Yes | `engineering_session.json` (R8-5, 2026-04-20) — 기사 seal 완료 시 최신 세션 요약. Edge pub / GB sub(edge_engineering_history 저장) / VW sub(fleet 히트맵 RO) |
| `fleet/engineering_diff/{ven_id}` | EdgeAgent | GridBridge · VWorld | 1 | No | `engineering_diff.json` (R8-5) — 이전 세션 대비 변경 이벤트 (techs_added/removed + config_changes JSON Pointer). GB 가 append-only 이력 저장 |
| `fleet/bundle/notify/{ven_id}` | GridBridge | EdgeAgent | 1 | No | 새 번들 버전 발행 알림 (R13-M1). Edge 수신 시 `BundleClient.sync()` 즉시 트리거. 페이로드: `{"version":"1.4.0","download_url":"...","sha256":"...","priority":"normal","published_at":"ISO8601"}`. retain=No (재기동 시 polling 으로 최신 확인) |

### GB → VW

| 토픽 | QoS | Retain | 설명 |
|------|:---:|:---:|------|
| `gridbridge/status/{group_id}` | 1 | Yes | ESG/권역 그룹 집계 감축 현황(30초) |

### 외부 신호 (Edge 구독)

| 토픽 | 발행자 | 구독자 | QoS | Retain | 설명 |
|------|:---:|:---:|:---:|:---:|------|
| `external/smp` | (데이터 공급자) | EdgeAgent | 1 | Yes | 원/kWh, 숫자 또는 `{"value": n}` |
| `external/temp/{ven_id}` | (데이터 공급자) | EdgeAgent | 1 | Yes | 외기온 °C |

## 페이로드 형식

- 모든 페이로드는 **UTF-8 JSON**
- 스키마는 `schemas/` 디렉토리에 JSON Schema(draft 2020-12)로 정의
- 미지정 필드는 무시(forward-compat). 스키마에 없는 필드는 **수신자가 무시**한다.

## kind 기반 라우팅 (GB)

`gridbridge/command/*` · `gridbridge/schedule/*`는 GB가 venues 레지스트리를 조회해 **`kind=dispatch`인 VEN 에 한해** 발행한다. 관측형(`kind=telemetry`)은 DB의 참여 기록만 생성되고 토픽 발행은 스킵된다.

## ven_id 네이밍 규칙

| 접두 | 용도 | 예 |
|------|------|----|
| `VEN-STORE-` | 관측형 편의점(DB replay) | `VEN-STORE-001` |
| `VEN-EP-` | E+ 가상 수용가 | `VEN-EP-OFFICE-01` |
| `VEN-REAL-` | 실 설비(BACnet/Modbus) | `VEN-REAL-BLDG-01` |
| `VEN-TEST-` · `VEN-E2E-` | 테스트·CI용 | `VEN-E2E-003` |

대문자·숫자·하이픈만 허용. 전 계층에서 대소문자 구분 없이 처리하되 저장은 대문자로 정규화.

## ACL (mosquitto passwd + ACL 파일)

각 Edge는 자기 `ven_id` 토픽에만 접근:

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
topic read  fleet/provision/VEN-STORE-001
topic write fleet/provision_ack/VEN-STORE-001
topic write fleet/engineering/VEN-STORE-001
topic write fleet/engineering_diff/VEN-STORE-001
topic read  external/smp
topic read  external/temp/VEN-STORE-001
```

GB·VW 쪽 ACL:
- GB: `topic read fleet/engineering/+` + `topic read fleet/engineering_diff/+` (edge_engineering_history 저장)
- VW: `topic read fleet/engineering/+` (fleet 히트맵 RO)
- Phase C mTLS 전환 시 cert subject = ven_id 로 쓰기 권한 자동 제한.

## 협업 규칙 — 스펙 변경 프로토콜

- 변경 제안은 PR로. 양쪽 팀(VW/GB 측 · Edge 측) 리뷰 필수.
- **필드 추가는 Minor(v1.x)**, 필드 삭제·이름 변경은 **Major(v2.0)**.
- `$id` 또는 `version`을 반드시 증가시키고, CLAUDE.md §버전 표에 날짜와 사유 기재.
- 스펙에 없는 필드는 받는 쪽이 무시 — 하위 호환 보장.
