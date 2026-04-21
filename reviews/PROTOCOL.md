# Review Protocol v2.0 — Deadlock-Free Inter-Team Review

## 원칙

1. **아이템 단위 소유**: 모든 리뷰 아이템에 "공(ball) 소유자"가 정확히 1명
2. **파일 단위 분리**: 라운드별 별도 파일 → 머지 충돌 0
3. **Append-only 응답**: 기존 응답 수정 금지, 새 상태 전이를 추가만
4. **3일 규칙**: OPEN/ACK 상태로 3일 초과 시 STALE 플래그

## 상태 머신

```
OPEN ───→ ACK ───→ RESOLVED ───→ CLOSED
  │                    │
  │                    └──→ DISPUTED ──→ RESOLVED ──→ CLOSED
  │
  └──→ WITHDRAWN
```

| 상태 | 공 소유자 | 의미 |
|------|-----------|------|
| OPEN | Receiver | 리뷰 등록됨, 수신팀 확인 대기 |
| ACK | Receiver | 수신팀이 확인함, 작업 중 |
| RESOLVED | Author | 수신팀이 해결책 제시, 등록팀 검증 대기 |
| DISPUTED | Receiver | 등록팀이 해결책 거부, 수신팀 재작업 |
| CLOSED | - | 등록팀 수락. 종료. |
| WITHDRAWN | - | 등록팀 철회. 종료. |

## 전이 규칙

| From | To | 누가 | 조건 |
|------|----|------|------|
| OPEN | ACK | Receiver | "검토 시작" 선언 |
| OPEN | WITHDRAWN | Author | 불필요해짐 |
| ACK | RESOLVED | Receiver | 수정 완료 + 커밋 해시 명시 |
| RESOLVED | CLOSED | Author | 검증 통과 |
| RESOLVED | DISPUTED | Author | 검증 실패, 사유 명시 |
| DISPUTED | RESOLVED | Receiver | 재수정 완료 |

## Deadlock 불가능 증명

- 각 아이템의 공은 항상 한 팀에만 존재
- 양 팀은 서로 다른 라운드 파일을 동시에 편집
- 같은 라운드 파일도: Author는 RESOLVED→CLOSED/DISPUTED만, Receiver는 OPEN→ACK→RESOLVED만 편집
- 양 팀이 동시에 "상대방 대기" 상태 = 불가능 (아이템 단위로 공이 분배되므로)

## Staleness 규칙

| 상태 | 경과 | 플래그 |
|------|------|--------|
| OPEN | > 3일 | STALE: Receiver 미확인 |
| ACK | > 5일 | BLOCKED: 작업 지연 |
| RESOLVED | > 3일 | STALE: Author 미검증 |
| DISPUTED | > 5일 | ESCALATE: 합의 필요 |

## 세션 시작 체크리스트

```
1. reviews/INDEX.md 읽기
2. 이 팀이 Owner인 아이템 중:
   - OPEN > 3일 → 즉시 ACK 또는 WITHDRAWN 요청
   - ACK > 5일 → 진행 상황 코멘트
3. STALE 있으면 새 작업보다 우선 처리
```

## 파일 구조

```
energy-contracts/
├── REVIEW.md           ← 레거시 (R1~R12 아카이브, 읽기 전용)
└── reviews/
    ├── PROTOCOL.md     ← 이 문서
    ├── INDEX.md        ← 전체 라운드 요약 테이블
    ├── TEMPLATE.md     ← 새 라운드 생성용 템플릿
    ├── R13.md          ← 개별 라운드 (예시)
    └── ...
```

## 수정(Amendment) 규칙

- OPEN/ACK 상태에서 Author가 이슈 내용을 수정할 수 있음 (아직 작업 시작 전)
- ACK 이후 수정 시 → 새 아이템으로 추가 (기존 것은 WITHDRAWN)
- RESOLVED 이후에는 Author가 내용 수정 불가 (DISPUTED로 재요청)
