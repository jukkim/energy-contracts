# SSOT Compliance Contract — energy-contracts 소비 폴더 의무

> 이 repo(`energy-contracts/schemas/`)는 워크스페이스의 **canonical 에너지 값 단일 root** 다.
> 배출계수·1차에너지 환산계수·ZEB baseline·시장가격을 쓰는 **모든 폴더·세션은 본 계약을 준수**한다.

## 1. 철칙 — 손편집 금지, 단일 root 파생

canonical 값(아래)은 **`energy-contracts/schemas/*.json` 한 곳에서만** 정의한다. 소비 코드는 숫자 리터럴을 박지 말고 **생성본 `_generated_constants.{py,ts}` 에서 import/파생**한다.

| 값 | 정본 스키마 |
|----|------------|
| 배출계수 (전력 0.4173 / 가스 0.2036 / 지역난방 0.126) | `emission_factors.json`, `energy_units.json` |
| PE 환산계수 (2.75 / 1.1 / 0.728 / 0.937) | `energy_units.json`, `energy_constants.json` |
| ZEB baseline 150 / 등급 | `energy_constants.json` (`zeb`) |
| 시장가격 (KAU 20000 / SMP 120·115 / tariff 87.3·140.2·222.3 / REC 71000) | `market_prices.json` |

**금지**: `CO2_FACTOR = 0.4173` 같은 손편집 리터럴, "be-3d 와 동기화" 식 수동 미러 신규 생성, 폐기 구값(0.4594·0.459·0.202·0.115·17000·61.6/109/191·65000) 사용.

## 2. 값 변경 절차

1. `schemas/*.json` 수정 (유일 손편집 지점)
2. `python scripts/gen_constants.py --all` (전 consumer `_generated_constants.*` 재생성)
3. EC PR 머지 **먼저** (consumer drift CI 가 EC `master` 비교)
4. 각 consumer regen 파일 commit (consumer별 PR) — `gen_constants.py --check` 0 drift 확인

## 3. 새 소비 repo 연결

- `scripts/gen_constants.py` 의 `PROJECT_TARGETS` 에 `{python|ts 경로, exports 화이트리스트}` 등록 → `--all`.
- ⚠ `schemas_hash()` 가 `gen_constants.py` self-bytes 포함 → **어떤 편집도 기존 전 consumer SOURCE_HASH cascade** 강제. 변경을 batch 로 묶어 cascade 1회.
- TS codegen 파이프라인 없는 web(Next.js 등) = guarded **mirror** + `verify_*_mirror.py`(canonical 일치) CI 게이트로 대체.

## 4. 강제 게이트 (우회 금지)

- **EC pre-commit**: `validate_ssot.py` — 폐기 구값 코드 잔재 차단(`--check canonical`) + codegen 입력 스키마 `_usage∈{codegen,hybrid}` 강제.
- **consumer CI**: `.github/workflows/ssot-drift.yml` — `gen_constants.py --check` 가 EC master 와 drift 시 차단. **신규 consumer 는 이 workflow 추가 의무.**
- **pre-commit lockstep**: sibling `_generated_constants` SOURCE_HASH 불일치(부분 regen) 차단.
- `--no-verify` 우회 지양. 불가피하면 사유 명시.

## 5. 값 정정 시 — 맥락 확인 (bulk-edit-verify)

scan N건 ≠ N건 수정. occurrence별 맥락 판정. 예: `제2024-1026호`는 **PE 환산계수 출처=정당(불변)** / **ZEB baseline 출처=구값(→ 제2025-738호)**. 일괄 치환 금지.

---
*신설 2026-06-23. Claude 세션 측 트리거 룰: `~/.claude/rules/ssot-canonical-compliance.md`. 값 SSOT: `~/.claude/ENERGY_SSOT.md`.*
