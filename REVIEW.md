# energy-contracts 리뷰 로그

스키마/프로토콜 변경 시 리뷰 결과를 여기에 기록한다.  
양쪽 팀이 확인 → 합의 → 수정 → 체크 표시.

> ⚠️ **이관 안내 (2026-04-21 이후)**: 신규 리뷰 라운드는 **`reviews/INDEX.md` + `reviews/R{N}.md`** 가 SSOT 다 (R13~). 본 파일은 **R1~R12 아카이브**.
> 본 파일 하단의 미체크 `[ ]` 박스 중 일부는 이관 시점 동결로 **stale** — 권위 상태는 `reviews/` 참조:
> - **R12 5건** → `reviews/R13.md` 에서 5/5 **CLOSED** (commit `30259eb`).
> - **R11 P4/P5** (line ~1028) → 같은 파일 line ~1059 "P3·P4·P5 완료" 로 이미 closed.
> - **R6-8 mTLS** 등 `RPi 5 실기 대기` 항목은 하드웨어 블록으로 **정당하게 미해결**.

---

## 미해결 항목 (2026-09-19 분할 시점 — 권위 상태는 `reviews/`)

| 항목 | 내용 | 상태 | 본문 |
|---|---|---|---|
| R6-8 | mTLS 프로비저닝 실증 (RPi 5 실기 + 인증서 자동 발급) | 하드웨어 대기 (R9-4 에서 Phase D 강등) | [R1~R6](docs/legacy/REVIEW/REVIEW_R1-R6_2026-04-19.md) |
| R9 실행 단계 4·5 | RPi 5 Tailscale 설치 + MQTT IP 전환 · E2E 왕복 검증 | Edge · RPi 5 실기 대기 | [R7~R12](docs/legacy/REVIEW/REVIEW_R7-R12_2026-04-19_to_04-21.md) |
| R10 Phase 4.2 | Monitoring Fleet tap | R10-3 답변 후 착수 | [R7~R12](docs/legacy/REVIEW/REVIEW_R7-R12_2026-04-19_to_04-21.md) |

R11 P4/P5 · R12 5건은 위 안내대로 이미 닫혔다(stale 체크박스).

## 목차 — 옮긴 라운드 (원문 그대로, 2026-09-19 분할)

| 절 | 파일 |
|---|---|
| 2026-04-19 v1.1 리뷰 · 라운드 2~6 (R1~R6, 라운드 5·6 finalize · R2 M2-2 unblock 포함) | [docs/legacy/REVIEW/REVIEW_R1-R6_2026-04-19.md](docs/legacy/REVIEW/REVIEW_R1-R6_2026-04-19.md) |
| 2026-04-19~21 라운드 7~11 · R12 · 리뷰 요청 템플릿 | [docs/legacy/REVIEW/REVIEW_R7-R12_2026-04-19_to_04-21.md](docs/legacy/REVIEW/REVIEW_R7-R12_2026-04-19_to_04-21.md) |

새 리뷰 라운드는 `reviews/INDEX.md` + `reviews/R{N}.md` 에 쓴다 (`reviews/PROTOCOL.md`).
