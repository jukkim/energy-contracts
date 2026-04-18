# CLAUDE.md — Energy Contracts (공유 스펙)

## 목적

VWorld(L1), GridBridge(L2), EdgeAgent(L3) 3개 프로젝트 간 **인터페이스 계약서**.
각 프로젝트는 이 스펙을 참조하여 독립 개발하되, 호환성을 보장한다.

**이 프로젝트는 코드가 아닌 스펙 문서이다. 구현은 각 프로젝트에서 한다.**

## 규칙

1. **스펙 변경 시 반드시 이 프로젝트에 먼저 반영** → 각 프로젝트가 참조
2. 스키마 필드 추가는 자유, **필드 삭제/이름 변경은 금지** (하위 호환)
3. 각 프로젝트 CLAUDE.md에 이 프로젝트 참조 명시
4. 버전 태그로 호환성 관리: `v1.0`, `v1.1` (minor = 필드 추가, major = 호환 깨짐)

## 디렉토리

```
energy-contracts/
├── CLAUDE.md              ← 이 파일
├── schemas/               ← JSON Schema (SSOT)
│   ├── reduction_schedule.json   — 감축 스케줄
│   ├── dr_event.json             — DR 이벤트
│   ├── telemetry.json            — 텔레메트리
│   └── control_command.json      — 제어 명령
├── openapi/               ← API 스펙 (OpenAPI 3.0)
│   ├── vworld-api.yaml           — L1 공개 API
│   ├── gridbridge-api.yaml       — L2 공개 API
│   └── edge-api.yaml             — L3 공개 API
├── protocols/             ← 프로토콜 규칙
│   ├── mqtt-topics.md            — MQTT 토픽 네이밍
│   └── openleadr-profile.md      — OpenADR 프로파일
└── examples/              ← 예제 JSON
    ├── schedule-simple.json
    ├── schedule-weekday.json
    └── telemetry-sample.json
```

## 버전

| 버전 | 날짜 | 변경 |
|:---:|:---:|------|
| v1.0 | 2026-04-19 | 초기 스펙: 감축 스케줄, DR 이벤트, 텔레메트리, 제어 명령 |

## 참조하는 프로젝트

| 프로젝트 | 경로 | 역할 |
|---------|------|------|
| VWorld | `projects/building-energy-3d/` | L1 — 스케줄 생성, 시각화 |
| GridBridge | `projects/gridbridge/` | L2 — 스케줄 배분, DR 정산 |
| EdgeAgent | `projects/edge-agent/` | L3 — 스케줄 실행, 텔레메트리 발행 |
