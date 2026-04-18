# MQTT 토픽 규칙

## 네이밍 컨벤션

```
gridbridge/{direction}/{ven_id}/{type}
```

## 토픽 목록

| 토픽 | 방향 | 발행자 | 구독자 | QoS | 설명 |
|------|:---:|:---:|:---:|:---:|------|
| `gridbridge/telemetry/{ven_id}` | Edge→GB | EdgeAgent | GridBridge | 1 | 5분 주기 설비 상태 |
| `gridbridge/command/{ven_id}` | GB→Edge | GridBridge | EdgeAgent | 2 | 즉시 제어 명령 |
| `gridbridge/schedule/{ven_id}` | GB/VW→Edge | GridBridge/VWorld | EdgeAgent | 2 | 감축 스케줄 |
| `gridbridge/ack/{ven_id}` | Edge→GB | EdgeAgent | GridBridge | 1 | 명령 수신 확인 |
| `gridbridge/alert/{ven_id}` | Edge→GB | EdgeAgent | GridBridge | 2 | 인터록 작동/장애 알림 |
| `gridbridge/status/{group_id}` | GB→VW | GridBridge | VWorld | 1 | 그룹 감축 현황 (30초) |
| `vworld/telemetry/{ven_id}` | EA→VW | EdgeAgent | VWorld | 1 | 직접 텔레메트리 (경로3, GB 경유 없음) |
| `vworld/alert/{ven_id}` | EA→VW | EdgeAgent | VWorld | 2 | 직접 알림 (인터록/장애, 경로3) |

## 페이로드 형식

모든 페이로드는 UTF-8 JSON. 스키마는 `schemas/` 디렉토리 참조:
- telemetry: `schemas/telemetry.json`
- command: `schemas/control_command.json`
- schedule: `schemas/reduction_schedule.json`

## Retained Messages

| 토픽 | Retain |
|------|:---:|
| telemetry | No (시계열, 실시간) |
| command | Yes (재접속 시 마지막 명령 수신) |
| schedule | Yes (재접속 시 현재 스케줄 수신) |
| status | Yes (대시보드 초기 로드) |
