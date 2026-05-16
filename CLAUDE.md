# CLAUDE.md — Energy Contracts (공유 스펙)

> **SSOT 허브** — Tier 2 도메인 계약. 변경 시 `myjob/docs/SSOT_GOVERNANCE.md` 절차 준수. 검증: `python scripts/validate_ssot.py`.

## 목적

VWorld(L1), GridBridge(L2), EdgeAgent(L3) 3개 프로젝트 간 **인터페이스 계약서**.
각 프로젝트는 이 스펙을 참조하여 독립 개발하되, 호환성을 보장한다.

**이 프로젝트는 코드가 아닌 스펙 문서이다. 구현은 각 프로젝트에서 한다.**

## 통신 경로 (4개)

```
경로 0: 사용자 → VW     (브라우저/음성/텔레그램/카카오톡)
경로 1: VW → GB → EA   (ESG/DR 그룹 제어)
경로 2: VW → EA         (개별 건물 직접 제어)
경로 3: EA → VW         (직접 텔레메트리/알림)
경로 4: EA → GB → VW   (그룹 텔레메트리 집계)
```

```
사용자 (브라우저 🖥️ / 음성 🎤 / 텔레그램 💬 / 카카오톡 💬)
  │ 경로 0
  ▼
VWorld (L1) ──경로1──→ GridBridge (L2) ──→ EdgeAgent (L3) ×N
  │                                            │
  ├──────────경로2 (직접)─────────────────→     │
  │                                            │
  ◀──────────경로3 (직접 피드백)────────────     │
  ◀──────────경로4 (GB 경유)──── GridBridge ◀───┘
```

## 규칙

1. **스펙 변경 시 반드시 이 프로젝트에 먼저 반영** → 각 프로젝트가 참조
2. 스키마 필드 추가는 자유, **필드 삭제/이름 변경은 금지** (하위 호환)
3. 각 프로젝트 CLAUDE.md에 이 프로젝트 참조 명시
4. 버전 태그로 호환성 관리: `v1.0`, `v1.1` (minor = 필드 추가, major = 호환 깨짐)
5. **변경 제안은 PR로**. VW/GB 측과 Edge 측 양쪽 리뷰 후 머지. 스펙에 없는 필드는 수신자가 무시(forward-compat).

## 수용가(VEN) 분류 용어

이 플랫폼은 수용가를 운영 모드 기준으로 이분한다:

| 분류 | 한글 용어 | 영문 용어 (스키마 `kind`) | 대표 예 | 제어 가능 | 데이터 |
|------|---------|--------------------------|--------|:---:|------|
| 관측형 수용가 | Telemetry VEN / Observable | `telemetry` | 편의점 220채 (DB replay) | X (read-only) | 단일 채널 시간별 |
| 제어형 수용가 | Dispatchable VEN | `dispatch` | E+ 가상, 실 설비(BACnet/Modbus) | O (양방향) | 다채널, Tier A 15+ 필드 |

GridBridge는 `venue.kind` 에 따라 `gridbridge/command/*`·`schedule/*` 발행을 분기(관측형 스킵). 구현 기술은 `backend: replay|energyplus|real_bas|virtual` 로 별도 기술한다.

### ESG 사전 정의 그룹

| group_id | 이름 | kind | 수량 | 용도 |
|----------|------|:---:|:---:|------|
| `ESG-STORE-100` | 편의점 100 (에너지) | telemetry | 100 | 실측 벤치마크 |
| `ESG-STORE-120` | 편의점 120 (센서) | telemetry | 120 | 센서 분석 |
| `ESG-EP-OFFICE` | E+ 가상 오피스 | dispatch | N | 제어 검증 |
| `ESG-EP-APT` | E+ 가상 아파트 | dispatch | N | 제어 검증 |

## 디렉토리

```
energy-contracts/
├── CLAUDE.md              ← 이 파일
├── schemas/               ← JSON Schema (SSOT)
│   ├── common.json               — 공용 enum·패턴 (Strategy M00~M15)   [v2.0]
│   ├── ems_strategies.json       — EMS 전략 코드표 + DR매핑 + 레거시   [v2.0 신규]
│   ├── emission_factors.json     — CO2 배출계수 (KR/ID, Scope 1/2)     [v2.0 신규]
│   ├── energy_constants.json     — PE factor, ZEB, 등급, 기후 기준값   [v2.0 신규]
│   ├── market_prices.json        — KAU, SMP, 전기요금, REC, PPA        [v2.0 신규]
│   ├── building_archetypes.json  — B01~B17, 용도매핑, EUI, 리트로핏    [v2.0 신규]
│   ├── region_codes.json         — C01~C11, H_A~H_G, 일사량            [v2.0 신규]
│   ├── dr_event.json             — DR 이벤트 (GB 생성)
│   ├── reduction_schedule.json   — 감축 스케줄 (VW/GB → Edge)
│   ├── control_command.json      — 제어 명령 (VW/GB → Edge)
│   ├── telemetry.json            — 텔레메트리 (Edge → GB/VW)
│   ├── venue.json                — 수용가 레지스트리 (GB SSOT)          [v1.1]
│   ├── virtual_prosumer.json     — E+ 가상 수용가 I/O 계약 (Edge)       [v1.0]
│   ├── control_response.json     — 제어 결과 (Edge → GB/VW)             [v1.0]
│   ├── edge_registration.json    — Edge 자동 등록 메타 (Edge → GB)      [v1.1]
│   └── edge_status.json          — heartbeat + 설비·드라이버 (Edge)     [v1.0]
├── protocols/             ← 프로토콜 규칙
│   ├── broker-architecture.md    — MQTT 브로커 배포·인증·Edge 유형 (VW)
│   ├── mqtt-topics.md            — 토픽·QoS·retain·ACL·네이밍 (통합)
│   └── openleadr-profile.md      — OpenADR 프로파일 (레거시)
├── openapi/               ← API 스펙 (미정)
└── examples/              ← 예제 JSON
    ├── schedule-simple.json
    ├── schedule-weekday.json
    └── telemetry-sample.json
```

## 작성 책임 분담

| 영역 | 작성 주체 | 리뷰어 |
|------|:---:|:---:|
| dr_event · reduction_schedule · control_command · broker-architecture | VW/GB 팀 | Edge 팀 |
| telemetry(보강) · control_response · virtual_prosumer · edge_registration · edge_status | Edge 팀 | VW/GB 팀 |
| mqtt-topics (통합) · venue · CLAUDE.md | 양쪽 공동 | 전원 |

## 버전

| 버전 | 날짜 | 변경 |
|:---:|:---:|------|
| v1.0 | 2026-04-19 | 초기 스펙: 감축 스케줄, DR 이벤트, 텔레메트리, 제어 명령 |
| v1.1 | 2026-04-19 | **관측형/제어형 이분화**. Edge측 스펙 4종 추가(virtual_prosumer, control_response, edge_registration, edge_status). venue.json 신설(kind+backend). mqtt-topics에 fleet/register · ACL · ven_id 네이밍 추가. |
| v2.0 | 2026-05-16 | **4-Module SSOT 확장**. EMS 코드 M0~M8→M00~M15 (16전략). 6개 공유 스키마 신설: ems_strategies(전략코드표), emission_factors(배출계수), energy_constants(PE/ZEB/등급), market_prices(시장가), building_archetypes(건물유형·EUI), region_codes(도시·HVAC). Layer 0(ENERGY_SSOT.md)→Layer 1(이 프로젝트)→Layer 2(각 프로젝트 constants) 3계층 거버넌스 확립. |
| v2.0.1 | 2026-05-16 | **통합 전략표 확정**. BuildWise+DR 의미 충돌 해소. M00=Baseline 공통화. 16 전략 단일 코드표: BuildWise(M00~M06,M11~M13), DR Control(M00,M01,M02,M04,M07~M09,M14~M15). M10=reserved. |

## 참조하는 프로젝트

| 프로젝트 | 경로 | 역할 |
|---------|------|------|
| VWorld (M1) | `projects/building-energy-3d/` | L1 — 스케줄 생성, 시각화, 직접 제어(경로2), 텔레메트리 수신(경로3) |
| GridBridge (M1) | `projects/gridbridge/` | L2 — 스케줄 배분, DR 정산, 텔레메트리 집계(경로4) |
| EdgeAgent (M2) | `projects/edge-agent/` | L3 — 스케줄 실행, 텔레메트리 발행(경로3,4) |
| AI Engine (M3) | `8.simulation/` | 배출계수·EMS전략·건물유형·PE factor 참조 (v2.0) |
| Agent Platform (M4) | 신규 (아이로) | 전략코드·등급·시장가·리트로핏 참조 (v2.0) |
