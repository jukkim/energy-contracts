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

## 6. 절감 부호·에너지 범위(scope) 표기 관례 (ADR-015, 2026-07-18)

**SSOT = `8.simulation/ems_transformer/docs/adr/ADR-015-sign-scope-convention.md`.** 새 필드·새 도구·새 스키마 설계 시 의무:

- **이름이 부호를 결정**: `*_delta_*` = 적용후−baseline (**음수=절감**) / `*_savings_*`·"절감" = baseline−적용후 (**항상 양수**, IPMVP) / `abatement_cost_*` = 음수=순절감 (MACC 표준). 같은 응답에 두 이름 혼용 금지.
- **사람 대면 표기**: 부호 있는 원시값 노출 금지 — "X% 절감/증가" 동사+양수로 변환 (F14 MCP `presentation.human_summary` 패턴).
- **scope 동봉**: 정량 델타에는 범위 enum(`site_total`/`electricity`/`gas`/`cooling_electricity`/`primary_energy`) 또는 범위 명사("냉방 전기의 X%")를 반드시 동반.
- 스키마 delta 필드 신설 시 description 에 부호 방향·scope 명문화 (기존 스키마 소급은 다음 개정 시 cascade 1회로 batch).

## 7. 이름 정본 — E→M 코드표 · 공조 방식 이름 (2026-09-15, v0.3.57)

**원인**: 같은 사실을 여러 곳에 손으로 적었다. E→M 은 `legacy_ems_code_mapping.json` 과 `ems_strategies.json#gcs_e_codes`
두 벌이었고, 둘을 대조하던 `check_legacy_code_consistency` 는 **없는 경로**(`legacy["deprecated_e_codes"]`)를 읽어 빈 표와
비교했다 — 한 번도 아무것도 비교하지 않고 초록이었다. 공조 방식 이름은 정본 필드가 없어 region_codes·매트릭스·be-3d·canvas 가 각자 들었다.

**정본**
- E→M = `legacy_ems_code_mapping.json#deprecated_e_codes` 하나. `components` = 뜻(다중 M), `maps_to` = 대표(같은 전략 → 그것,
  없으면 최소 상위집합, `exact=false`). `gcs_e_codes` 는 `gen_constants.py --all` 이 만드는 **투영**.
- 공조 방식 이름 = `region_codes.json#hvac_types[*].name_kr` 하나(+`aliases`). be-3d 는 생성본 `HVAC_NAME_KR`, canvas 는 가드된 미러,
  `hvac_ems_matrix.json` 은 행 키 → 정본 코드만 적는다.
- 게이트 = `validate_ssot.py --check schemas` 의 `check_legacy_code_consistency` · `check_e_code_emitter_coverage` · `check_hvac_display_names`
  (+ 기존 `gen_constants.py --check`). 시험 = `tests/test_naming_ssot_gates.py`.

### 7.1 E-code (번호 체계 = 2026-05-03 리매핑 이후 통합 metadata 번호 — reverse Module B 가 내보내는 번호)

행 실측 = 2026-09-15 `8.simulation/ems_transformer/data/unified/metadata_unified.jsonl` 의 `_migration.e_to_m.from` 별 source·npy_dir 집계.

| 코드 | 정본 components (maps_to) | 이전 정본 | 근거 |
|---|---|---|---|
| E0 | M00 | M00 | `ems_transformer/scripts/unify_phase_data.py:30` baseline→E0 |
| E1 | M06 | M06 | 같은 파일 :31 m0→E1 NightCycle |
| E2 | M01 | M01 | :32 m1→E2 · RVK `RVK_*_M01_*`→E2 |
| E3 | M02 | M02 | :33 |
| E4 | M03 | M03 | :34 |
| E5 | M07 | **M10** | 5,999행 전부 source=phaseC · `PC_*_m12` · :41 m12→E5 DCV · `reverse/scripts/build_rvk_metadata.py:32` M07→E5. "DemandLimiting" 은 GCS 생성기 `generate_ems_idfs.py:876` 의 뜻, 그 번호 행 0건(`fix_gcs_ems_codes.py:10`) |
| E6 | M08 | **M04** | 6,718행 source=phaseC · `PC_*_m13` · :42 m13→E6 HeatRecovery. "PMV 0.5" 는 생성기 `apply_e6`(:1190), 그 행 23,228건은 E7 로 이동 |
| E7 | M04 | M04 | :35 m4→E7 |
| E8 | M06+M02 (M14, 비정확) | **M11** | 6,000행 source=phase_b1 · `B1_*_m9` · :40 m9→E8. "Eco+Staging" 은 생성기 `apply_e8`(:1201) → E10 으로 이동 |
| E9 | M02+M03+M04 (M12, 비정확) | M12 | 생성기 `apply_e9`(:1213) 60,254건 전량 E11 로 이동, 현재 0행 |
| E10 | M02+M03 (M11, 비정확) | M11 | `ems_simulation/scripts/generate_idf.py:757` "M6: M2 + M3 복합, M1 제외" · `reverse/configs/data_spec.yaml` e_to_m |
| E11 | M02+M03+M04 (M12, 비정확) | M12 | `generate_idf.py:772` |
| E12 | M05 | M05 (gcs 표에 없음) | :36 m5→E12 |
| E13 | M02+M03+M05 (M13, 비정확) | M13 (gcs 표에 없음) | `generate_idf.py:806` |

### 7.2 공조 방식 (IDF = `8.simulation/mpc_model/energy_predictor/idf_templates/buildings`, 객체 단위 파싱 수)

| 코드 | 정본 name_kr | 이전에 갈라진 표기 | IDF 실측 |
|---|---|---|---|
| H_A | 중앙집중식 VAV 공조(냉동기·보일러) | be-3d A "팬코일+냉동기" · 정책평가 A "Window AC" | B01: Chiller 2 · Boiler 2 · VAV 재열 15 / B08: Chiller 1 · Boiler 1 · VAV 41 (B07 은 냉동기 대신 DX 4) |
| H_B | 패키지형 VAV 공조(DX 냉방·전기 재열) | region_codes·be-3d "중앙식 FCU" · 정책평가 "Split AC" | B01: Chiller 0 · Boiler 0 · DX TwoSpeed 4 · VAV 재열 16 · 전기코일 20 / B08: DX 9 · VAV 46 · 전기코일 46 |
| H_C | 패키지형 단일존 공조(PSZ) | be-3d C "VAV 중앙공조" · 정책평가 "Packaged Rooftop" | B02: 단일존 히트펌프(UnitaryHeatPump:AirToAir) 15 · DX 15 · 가스 보조코일 15 |
| H_D | 시스템에어컨 냉난방(VRF·EHP) | be-3d·매트릭스 HD "온돌+VRF" · 정책평가 D "VAV" | B02: VRF 실외기 3 · 실내기 15, 보일러 0 / B16: 실외기 1 · 실내기 27 |
| H_E | 온돌(중앙 가스보일러) + 벽걸이 에어컨 | be-3d E "지역냉난방" · HE "온돌+지역난방" · 매트릭스 E "Hydronic radiant + DOAS" | B16: Boiler 1 · 온돌(LowTemperatureRadiant) 24 · PTAC 27 |
| H_F | 시스템에어컨 냉방 + 가스보일러 난방 | be-3d HF "온돌+개별보일러" · 매트릭스 HF "Hybrid (central + 온돌)" · 정책평가 HF "District Heat + AC" | B02: Boiler 1 · VRF 실내기 15 · 온수 방열기 15 / B16: Boiler 1 · VRF 27 · 온돌 26 |
| H_G | 지역난방 + 건물별 냉방 | "지역난방+개별냉방" · be-3d HG "온돌+축열" · 매트릭스 HG "gas-fired boiler + radiator" | 보일러 0, DistrictHeating 1~2. 냉방은 원형 유지 — B01: Chiller 2 · VAV 15 / B02·B16: PTAC 15·27 |

**외부 용어** (국가법령정보센터): 「건축물의 에너지절약설계기준」 제5조 — "중앙집중식 냉·난방설비"(가정용 가스보일러는 개별 난방설비로 간주),
"이코노마이저시스템", "대수분할운전", "열회수형환기장치", 같은 고시 — "지역난방공급방식", "팬코일유닛"
(https://www.law.go.kr/LSW/admRulLsInfoR.do?admRulSeq=2100000282390). 「효율관리기자재 운용규정」 — "멀티전기히트펌프시스템"(EHP),
"전기냉방기"(KS C 9306) (https://www.law.go.kr/LSW/admRulLsInfoR.do?admRulSeq=2100000279914). KS·대한설비공학회 용어집은 이 세션에서 조회하지 못했다.

**남은 일(데이터·서빙, 이 릴리스 밖)**: ① 2026-05-29 `migrate_metadata_e_to_m.py` 가 옛 정본으로 옮긴 행 — E5 5,999→M10 · E6 6,718→M04 · E8 6,000→M11
재라벨 필요. ② gcp 출처 E10 132,814행 중 리매핑분 67,174행 외 65,640행의 원래 뜻(생성기 E10 = PMV 0.7 포함) 미확인.
③ F14 `find_unsupported_combos` 는 `matrix.get(pv.hvac_type)` 라 `H_A`~`H_G` 표기 요청은 매트릭스 행이 없어 호환 검사를 건너뛴다.

---
*신설 2026-06-23. §6 추가 2026-07-18 (ADR-015). Claude 세션 측 트리거 룰: `~/.claude/rules/ssot-canonical-compliance.md`. 값 SSOT: `~/.claude/ENERGY_SSOT.md`.*
