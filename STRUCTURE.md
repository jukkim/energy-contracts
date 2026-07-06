# 폴더 구조 및 파일명 규칙 (STRUCTURE.md)

> **트리거**: 파일/폴더 생성·이동 시 준수 (project-structure-guard). 신규 스키마는 codegen 파이프라인 준수.
> **AI 챔피언 그룹 C — Tier-2 SSOT 허브**. 배출계수·PE·ZEB·시장가 등 전 23 폴더 canonical 상수의 단일 root. 상위 = `공모전/2026-04-24_AI챔피언_전국민AI경진대회/docs/FOLDER_GROUPS.md`.

## 서브폴더별 규칙

| 폴더 | 역할 | SOURCE / GENERATED |
|------|------|------------------|
| `energy_contracts/schemas/` | **JSON 스키마 (SOURCE, ~60)** — emission_factors·energy_units·market_prices·zeb 등 | **SOURCE** (손편집 O, 여기가 진실) |
| `energy_contracts/_pydantic_models/` | 스키마→Pydantic 자동생성 (~60) | **GENERATED** (`gen_constants.py --all` 재생성, 손편집 금지) |
| `energy_contracts/{critics,dr_settlement,esg,rate_limit_policy,retry_policy,_utils}/` | 계약 로직 | SOURCE `snake_case` |
| `examples/` (+ `invalid/`) | 스키마 검증용 페이로드 예시 | `snake_case.json` |
| `protocols/` | 프로토콜 정의 | `snake_case` |
| `scripts/` | `gen_constants.py`(codegen)·`validate_ssot.py`(게이트) | `snake_case.py` |
| `docs/` (+ `adr/`·`legacy/`) | 문서 | ADR=`ADR-{NNN}-{kebab}.md`, 스펙=`UPPER_SNAKE.md` |
| `reviews/` | 코드리뷰 아카이브 (미사용 시 `docs/legacy/`로) | — |
| `tests/` | 테스트 | `test_*.py` |

## ⚠ 절대 규칙 (SSOT 무결성)

- `schemas/*.json` = **canonical 진실. 절대 삭제 금지.** 값 변경 = 여기 수정 → `gen_constants.py --all` → `validate_ssot.py` → 소비 repo 휠 재핀.
- `_pydantic_models/*.py`·`_generated_constants.py` = **생성물. 손편집 금지** (pin lockstep, 휠 SHA). 소비 repo 는 `from ..._generated_constants import` 만.
- 정합 강제 = `SSOT_COMPLIANCE.md` (pre-commit `validate_ssot.py`). **COUNTS_SSOT.yaml 불필요** — codegen 이 우월.

## 공통

- 명명: `snake_case`. 한글·공백 파일명 금지.
- git-ignored (삭제=재생성): `build/`·`dist/`(휠)·`.playwright-mcp/`·`.ruff_cache/`·`__pycache__/`.
- 캐논 수치(PE 2.75/1.1/0.728·배출 0.4173/0.2036/0.126·ZEB 150·시장가) = 여기가 SSOT. 산재 아님.

---
*작성 2026-07-06 (AI 챔피언 폴더 표준화). 상위 = FOLDER_GROUPS.md 그룹 C (SSOT 허브).*
