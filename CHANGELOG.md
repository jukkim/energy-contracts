# Energy Contracts — CHANGELOG

스키마·프로토콜 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

---

## 태그 v0.3.58 (2026-09-17) — 패키지 버전 0.3.58

> 아래 0.3.62 절(#147 한국 건축 기준값)과 #148(계보 봉투 사본 게이트 줄바꿈)을 담는 **릴리스 태그**다.
> 이 CHANGELOG 의 절 번호(0.3.59~0.3.62)는 패키지 버전·태그와 따로 매겨져 왔다 — 소비처 핀은 **태그 이름**을 쓴다.
> 소비처는 `scripts/bump_ec_pin.py v0.3.58` 로 pyproject 핀과 ssot-drift 워크플로 ref 를 함께 올린다(생성본 SOURCE_HASH 가 바뀌었다).

## 0.3.62 (2026-09-17)

> 릴리스 사유: **한국 건축 기준값이 SSOT 밖에서 손으로 적혀 있었고, 세 벌이 모두 현행 원문과 달랐다.**
> 사용자 지시 "최신 법령이어야 하고, 에너지 SSOT 를 점검·반영해야 한다. 고정값은 안 된다."

- **신규** `korean_building_standards.json` v1.0 (`_usage: codegen`) — law.go.kr 현행 원문(2026-09-17 조회)에 묶인 값:
  에너지절약설계기준(**고시 제2026-360호**, 2026.7.8) [별표 1] 열관류율 상한·기후지역 비고, [별표 8] 설계용 실내 온습도 ·
  건축물의 설비기준 등에 관한 규칙(국토교통부령 제1614호, 2026.8.24) 제11조·[별표 1의6] 필요환기량과 적용 대상 ·
  학교보건법 시행규칙(교육부령 제366호) [별표 2] 교실 21.6 ㎥/인·h · 제로에너지건축물 인증 기준(고시 제2024-893호) [별표 3] 26/20℃ ·
  한국에너지공단 제로에너지건축물 인증 제도 운영규정(2026.3.20) [별표 2] 용도프로필 23 종 · [별표 3] PE 계수(= `energy_constants.pe_factors` 일치 확인).
  원문 파일은 `docs/legal_sources/2026-09-17/`, 스키마에 sha256.
- **신규** `scripts/verify_korean_law_sources.py` — 원문 텍스트에서 숫자를 원문 순서로 뽑아 대조(병합 셀 대응표 포함), 용도프로필 HWP 전 필드 대조,
  현행성 기한(`currency.recheck_after_days`, 제안 90 일), 파생 복사본 일치. rc 0 통과 · 1 불일치 · 2 못 잼 · 3 기한 지남.
  `validate_ssot.py --check law`(all 에 포함)로 연결 — rc 1 만 커밋 차단. 변이 시험 16 종(`tests/test_korean_law_sources.py`).
  변이 시험이 대조기 결함 둘을 먼저 잡았다: 기후지역 정의를 첫 조각만 비교 · 원문 파일이 없으면 '못 잼' 대신 예외.
- `region_codes.json` v2.2 → **v2.3** (가산): C12~C18 `climate_zone` 등재(v2.1 이 '권위값 미확보'로 비워 둔 칸) +
  전 도시 `admin_region`·`climate_zone_source`. 전주 = 전북특별자치도 = **중부2**. `climate_zone` 에 enum.
- `simulation_scenarios.json` v1.0 → **v1.1**: `ko_envelope_uvalue` 를 원문으로 정정(중부2 지붕 0.17→0.15 · 제주 벽 0.36→0.41 등 13 칸).
  소비처는 없었다(생성 화이트리스트 밖). 필드는 지우지 않고, 대조기가 정본 파생값과의 일치를 강제한다.
- `gen_constants.py`: `KR_*` 10 종 생성, `8sim-shared` 화이트리스트에 등재. 다른 소비처는 SOURCE_HASH 만 바뀐다.

### 원문과 달랐던 것 (소비 저장소 `8.simulation/mpc_model/_shared/korean_standards.py`)

비주거 창 중부1 1.200(원문 1.300) · 주거 창 중부1 1.000(0.900) · 비주거 문 1.5/1.8/2.2/2.8(원문 1.5/1.5/1.8/2.2) ·
주거 현관문 남부/제주 1.8/2.2(원문 1.400) · 비주거 바닥 제주 0.350(0.330) · 전주 = 남부(원문 중부2).
머리말은 고시 제2024-1026호를, ENERGY_SSOT §7 은 제2025-738호를 가리켰다 — 현행은 제2026-360호.

---

## 0.3.61 (2026-09-16)

> 릴리스 사유: **요일이 결과를 좌우하는 입력이 됐는데 계보에 없었다.** 후처리가 주 시작 요일을
> 0(월)로 가정했으나 `eplusout.eio` 는 화요일을 기록한다 — 재실 마스크가 하루 통째로 밀렸고,
> 63 run 중 **50 run** 의 PMV 가 움직였다(warm 35 · cold 31 · 양쪽 16). 에너지와
> `period_hours` 는 **0 run** 이 움직였다. 값이 바뀐 이유를 사후에 설명할 수단이 없었다.

- `energyplus_run_manifest.json` v1.3 → **v1.4** (가산):
  - `$defs/Run/properties/comfort` 에 **선택** 항목 `start_dow_used`(0..6, 0=월)와
    `start_dow_source`. 요일은 재실 마스크에만 쓰이고 에너지에는 쓰이지 않으므로 comfort 의
    인자다.
  - `$defs/Run` 에 **선택** 항목 `eio_sha256`. `start_dow_used` 의 출처 파일이므로
    `input_idf_sha256`·`result_sha256` 과 같은 층이다.
- `required` 와 `additionalProperties:false` 는 **유지** — 옛 번들이 그대로 통과한다.
- ⚠ `start_dow_source` 는 **선언이다.** 생산자가 실제로 그 자리에서 읽었는지를 이 필드가
  증명하지는 않는다. 출처가 하나뿐인 동안은 무해하나 둘 이상이 되면 측정으로 바꿔야 한다.
  (생산자가 먼저 이 한계를 밝혔고, 그대로 스키마 description 에 적었다.)

### 생성본이 세 세대 동안 낡아 있었다

`_pydantic_models/energyplus_run_manifest.py` 에 **속성 20 개가 빠져 있었다** — v1.1 의 존
증거, v1.2 의 `clo`/`met`/extremum, v1.3 의 `period_hours` 가 전부. 그 세 PR 모두 스키마와
CHANGELOG 만 고쳤고, **재생성을 부르는 단계가 체인 어디에도 없다.** 스키마를 읽는 쪽은 맞고
모델을 import 하는 쪽은 틀린 채로 세 세대가 지났다.

- 이 스키마의 모델을 재생성해 커밋했다(다른 모델은 헤더의 임시 파일명만 바뀌어 되돌렸다).
- `tests/test_generated_models_track_their_schemas.py` — 스키마가 선언한 모든 속성이 생성본에
  나타나야 한다. 78 개 스키마 전수. 재생성하지는 않는다(codegen 은 느리고 헤더가 매번 달라진다);
  **필드가 통째로 빠지는** 이 사고의 모양만 잡는다.

---

## 0.3.60 (2026-09-16)

> 릴리스 사유: **`period: "annual"` 은 선언이고 아무도 재지 않았다.** 설계일 2일(48h)이 앞에 붙은
> CSV 를 전 행 합산한 매니페스트가 발행됐고(2026-09-16 B02 H_C·H_D·H_F, 0.60~0.82% 부풀림),
> 소비처는 그것을 잡을 수단이 하나도 없었다 — 오염이 **성분 합 = 총계**를 유지해 정합성 검사를
> 통과하고, 세 setpoint 가 같은 방향이라 단조성도 통과한다. 상류가 알려 주지 않으면 하류는 모른다.

- `energyplus_run_manifest.json` v1.2 → **v1.3** (가산): `$defs/Run` 에 **선택** 항목
  `period_hours` — 결과 창의 실제 길이(시간). `period` 선언과 대조해 8,808 이면 그 자리에서 빨강이다.
- `required` 와 `additionalProperties:false` 는 **유지** — 옛 번들이 그대로 통과한다.
- ⚠ 생산자 주의: `extract_energy` 의 반환 dict 에 넣으면 `facility_total = sum(totals.values())` 가
  이 값을 에너지로 더해 **총계를 오염시킨다**. run 수준에 별도로 싣는다.

---

## 0.3.59 (2026-09-16)

> 릴리스 사유: 0.3.58 이 실은 존 증거로 **귀속의 다섯 필드는 채워졌지만 둘이 비었다** — `clo`·`met`.
> 소비처(airos)의 게이트는 척도 밖 run 을 사람이 귀속할 때 극값 지점의 7개 값을 요구하는데, 그중 둘이
> 매니페스트에 없어 손으로 채울 수 없었다. 생산자 코드에는 있다(`met = 1.0 if residential else 1.2`,
> `clo = _clo_for_month(month)`).
>
> ⛔ **소비처가 그 규칙을 옮겨 적는 것으로 때우지 않는다.** 그것은 소비처가 재구성한 생산자 규칙이지
> 생산자가 보고한 값이 아니고, 계절 경계가 바뀌면 pin 이 조용히 어긋난다. 값을 가진 쪽이 싣는다.

- `energyplus_run_manifest.json` v1.1 → **v1.2** (가산): `$defs/ComfortExtremum` 에 **선택** 항목 셋 —
  `clo`(그 극값 시점의 착의량, 계절로 갈린다) · `met`(대사량, 주거 원형과 비주거가 다르다) ·
  `air_velocity_m_s`. 앞의 둘은 airos 게이트의 `DRIVER_FIELDS` 7개 중 남은 둘이고, 셋째는 PMV 입력
  삼총사를 한 자리에 모으기 위한 것이다(기존 귀속 기록에 이미 0.1 로 남아 있었다).
- `required`(zone·hour_index·ta_c·tr_c·rh_pct)와 `additionalProperties:false` 는 **유지** — 이미
  발행된 매니페스트가 그대로 통과한다.

---

## 0.3.58 (2026-09-16)

> 릴리스 사유: **PMV 는 값만으로 재현되지 않는다.** 입력 해시가 같아도 후처리 규칙이 바뀌면 값이 달라지는데,
> 매니페스트에 그 계보가 없었다. 실측 사건 — 표준 E+ 63 run 중 45가 ISO ±3 척도 밖이었고, 원인은 계산기가 아니라
> **존 선택**이었다(비공조 세탁실이 Ta 90.26 ℃ 로 자유부동해 `pmv_warmest 25.9546` 을 냈다). 어느 존이 극값을
> 몰았는지가 자료에 없어 소비처가 replay 로 되짚어야 했고, 그래서 귀속이 매니페스트가 아니라 재현 코드를 믿고 있었다.

- `energyplus_run_manifest.json` v1.0 → **v1.1** (가산): `$defs/Run/properties/comfort` 에 **선택** 항목 9개 —
  `zone_selection`(존을 고른 규칙) · `conditioned_zone_count` · `reported_zone_count` · `occupied_zone_hours` ·
  `postprocess_code_sha256`(후처리 코드 해시 — 이것이 없으면 규칙 변경이 해시로 드러나지 않는다) ·
  `warmest_at` · `coldest_at` · `zones_used` · `zones_excluded`.
  `$defs/ComfortExtremum` 신설(`zone`·`hour_index`·`ta_c`·`tr_c`·`rh_pct`) — 극값이 **어디서** 났는지가 있어야
  그 이탈이 비공조 존 탓인지(`not_applicable`) 실제 결과인지(`missing`) 갈린다.
- `required` 5필드와 `additionalProperties:false` 는 **유지**. 옛 번들은 그대로 통과하고, 스키마에 없는 필드는 계속 거부된다 —
  그 거부가 실제로 작동해 airos `sync_standard_eplus_bundle.py` 가 새 필드를 실은 번들을 막았고, 그래서 이 릴리스가 생겼다.
  생산자 = ems-transformer, 소비자 = airos-energy-decision(동기화·게이트)·mpc-model.

---

## 0.3.57 (2026-09-15)

> 릴리스 사유: 이름 정본 두 건 — **E→M 표가 두 벌**이었고 **공조 방식 이름이 소비처마다 달랐다.**
> 둘 다 원인은 같다: 같은 사실을 여러 곳에 손으로 적고, 대조 검사가 없거나(HVAC) **빈 비교로 초록**이었다(E→M).
> `gen_constants.py --all` 재생성 + `bump_ec_pin.py v0.3.57` 로 재핀한다. 근거 표 = `SSOT_COMPLIANCE.md` §7.

- `legacy_ems_code_mapping.json` v1.0.0 → **v1.1.0**: E→M **유일한 정본**. `deprecated_e_codes.*` 에 `components`(뜻, 다중 M)·`exact` 추가.
  E5 M10→**M07**(DCV) · E6 M04→**M08**(전열교환기) · E8 M11→**[M06,M02]**(maps_to M14) — 정본이 GCS 생성기 번호 뜻과
  통합 metadata 번호 뜻을 한 표에 섞어 적고 있었다(행 실측: E5=`PC_*_m12`, E6=`PC_*_m13`, E8=`B1_*_m9`).
  E10/E11/E13 은 maps_to 그대로 두되 `exact=false`(ems_simulation m6~m8 은 M1 제외 — `generate_idf.py:757`).
  `gcs_generator_codes`(생성기 원래 번호 기록) · `drift_guard.e_code_emitters`(E-code 를 내보내는 파이프라인 선언) 추가.
- `ems_strategies.json` v3.1 → **v3.2**: `legacy_mapping.gcs_e_codes` = 정본 `maps_to` **생성 투영**(E5·E12·E13 추가, E6·E8 정정).
  손편집 금지 — `scripts/legacy_e_codes.py` 를 `gen_constants.py --all` 이 먼저 돌려 맞춘다. `LEGACY_MAPPING` 소비자 값이 바뀐다.
- `region_codes.json` v2.1 → **v2.2** (`_usage` reference-only → **hybrid**): `hvac_types.*.name_kr` = 공조 방식 한국어 표시 이름의
  **유일한 정본**, `aliases`(A~G·HA~HG) 추가. H_B "중앙식 FCU" → **패키지형 VAV 공조(DX 냉방·전기 재열)**(IDF: 칠러·보일러 0,
  DX TwoSpeed + VAV 재열 + 전기 코일). H_G "개별냉방" → **건물별 냉방**(B01·B08 H_G 는 중앙 냉동기).
- `hvac_ems_matrix.json` v1.0.1 → **v1.1.0**: `hvac_types` 의 ASHRAE 문장 상수(HG="gas-fired boiler + radiator" 등 — 인코더·시뮬과 다른 설비)를
  **정본 코드 참조**(`A`→`H_A` … `HG`→`H_G`)로 교체. 셀 값은 그대로(A~E 행 주석이 ASHRAE 원형 기준인 점은 별건).
- `gen_constants.py`: be-3d TS 에 `HVAC_NAME_KR`(정본 코드·별칭 → name_kr) 생성. `regenerate_all` 이 gcs_e_codes 투영을 먼저 동기화.
- `validate_ssot.py`: `check_legacy_code_consistency` **재작성**(없는 경로를 읽어 한 번도 비교하지 않던 판 — 이제 로드 실패·빈 표·키 집합 차이·규칙 위반을
  전부 위반으로 센다) · `check_e_code_emitter_coverage`(reverse `data_spec.yaml` 의 e_labels·e_to_m 대조, 형제 부재 시 UNMEASURED 출력) ·
  `check_hvac_display_names`(name_kr·별칭 유일성·매트릭스 행→정본 코드). 시험 `tests/test_naming_ssot_gates.py` 16개(깨뜨려서 빨강 + 원본 초록).
- `validate_ssot._exempt_key`: `--pre-commit` 이 스테이징 파일 하나를 루트로 넘기면 면제 키가 `"/."` 가 되어 **파일 이름 면제가 전혀 안 먹었다**
  (SSOT 자체 `ems_strategies.json` 의 ems_simulation 구 코드 표가 9건으로 막힘). 파일 루트는 저장소 루트 기준으로 판정한다.
  ⚠ 이 커밋은 훅이 부르는 **공유 체크아웃(수정 전) 검사기**가 같은 오류로 막아 `--no-verify` 로 올렸다 — 워크트리 검사기로 strategy/schemas/usage·pytest 전부 통과 확인.

## 0.3.56 (2026-09-13)

> 릴리스 사유: 필지 규칙(2026-09-13 사용자 결정 — 1동 필지만 건물 값, 여러 동·모름은 값 없음 + 이유)을
> 에이전트 계약에 싣는다. `bump_ec_pin.py v0.3.56` 로 재핀한다(이번부터 CI 워크플로 pip 핀도 함께 바뀐다).

- `agent_contracts.json` v1.2 → **v1.3**: `BuildingContext.eui` 를 **선택·nullable**(기본 null)로, `value_withheld_reason`
  (string|null) 추가. 여러 동 필지처럼 이 건물의 값으로 쓸 수 없는 답을 404 대신 "eui=null + 이유" 로 돌려줄 수 있다.
  배분 추정·필지 합계로 채우지 않는다. 필수 해제·필드 추가만이라 기존 생산자(eui 를 늘 채우는 쪽)는 그대로 유효하다 — minor.
  ⚠ 소비자는 `ctx.eui` 가 None 일 수 있음을 다뤄야 한다(be-3d 는 null 답으로 바꿀 때 에이전트 가드를 함께 고친다).
- `forecast_response.json`·`anomaly_response.json` 의 `pnu` 설명 "건물 PNU" → **필지 PNU(19자리 — 필지 키)**.
- `ui_capabilities.json` `ui.counterfactual.backend`: "F9 /v1/counterfactual (KBEP)" → KBEP :8020 `/v2/counterfactual` 직접
  (게이트웨이 F9 는 노출되지 않는다 — 게이트웨이 반사실은 F14 fast-path 내부).
- `scripts/bump_ec_pin.py`: 소비 저장소 워크플로의 **pip 설치 핀**(`energy-contracts @ git+…@vX`)도 찾아 바꾸고 `--check` 로
  skew 를 잡는다(`CI_PIN_REPOS` = eduarena — pyproject 핀 없이 `pytest.yml` 한 줄로 설치한다). 시험 3개 추가.

## 0.3.55 (2026-09-12)

> 릴리스 사유: `agent_contracts.json` v1.2(에이전트 응답의 건물 식별 선택 필드 4개)를 소비 저장소에 싣는다.
> `bump_ec_pin.py v0.3.55` 로 재핀하고 agentleague·eduarena 생성 상수도 재생성한다. ingestion-worker 는 그 저장소 요청으로 보류.

- `agent_contracts.json` v1.1 → **v1.2**: `BuildingContext`·`BuildingForecast`·`DREnrollment`·`SetbackPattern`·
  `BenchmarkStats`·`FireRiskAssessment` 에 선택·nullable 필드 4개 — `building_mgmt_no`·`requested_building_mgmt_no`
  (25자리 `^[0-9]{25}$`)·`building_use_allowed`(boolean)·`metric_scope`(parcel|building). 기존 필드와 `required` 는 그대로다
  (추가만이라 minor). `BuildingContext.pnu` 설명을 "필지 키" 로 바로잡았다. be-3d 내부 에이전트가 25자리 건물 번호로
  물으면 이 필드로 "누구의 값인가" 를 답한다 — 19자리 요청의 응답은 전과 같다(새 필드 없음).
  `docs/DEFERRED_INTEGRATIONS.md` 2026-09-12 두 항목 해소, `docs/BUILDING_IDENTITY_VOCABULARY.md` 갱신.

## 0.3.54 (2026-09-12)

> 릴리스 사유: 소비자 6저장소가 이미 미릴리스 master(market_prices v2.1 · data_classification v1.2 `EvidenceDisplayClass` · korean_bb 핀 · 여권 v1.2)로
> 상수를 재생성해 v0.3.53 핀으로는 CI 가 전부 DRIFT(해시 9ef25a47 ≠ 1b887ba6). `bump_ec_pin.py v0.3.54` 로 일괄 재핀한다.
> `BuildingContext.building_mgmt_no` 는 여전히 보류(DEFERRED) — 이 릴리스에 없다.


- `building_passport.json` v1.1 → **v1.2**: `identity.identity_match_status` (exact/probable/unmatched) —
  packet `BuildingIdentity.selected_identifier_match_status` 와 같은 어휘. verified 만 exact 다.
- `agent_contracts.json` `BuildingContext` 는 여전히 `pnu` 만 받는다(**미변경, 보류**). 이 스키마는
  generated constants 의 원천이라 한 바이트 변경이 6개 소비 저장소의 태그 재핀(`bump_ec_pin.py`)을 부른다.
  `building_mgmt_no` 선택 필드는 다음 EC 태그 릴리스에 함께 싣는다 — `docs/DEFERRED_INTEGRATIONS.md`.
- 신설 `docs/BUILDING_IDENTITY_VOCABULARY.md` — be-3d/airos 상태 어휘 ↔ `BuildingIdentity` ↔ 여권 대응표와 5 원칙.

- `building_passport.json` v1.0 → **v1.1**: `identity` 에 `building_mgmt_no`(25자리)·`parcel_id`(19자리)·
  `physical_identity`(building/parcel/none) 를 추가한다. 여권의 주어는 필지가 아니라 **건물**이며,
  `pnu` 는 `parcel_id` 의 호환 별칭으로 남는다. `building_mgmt_no` 가 있으면 `parcel_id` 필수.
  AIROS `make_passport` 가 이미 내보내던 `residential_subtype`·`built_year`·`vintage_class`·`district` 도
  스키마에 등재한다(`additionalProperties:false` 였으므로 그동안은 이 값이 있는 여권이 계약 위반이었다).
  값 추가만이라 minor.
- `scripts/gen_pydantic_models.py --all` 이 `dictionary changed size during iteration` 으로 중간에
  죽던 것을 고쳤다(`walk()` 가 순회 중 루트 `$defs` 에 항목을 넣는다 — 스냅샷 순회). 그 때문에
  2026-08-07 스키마 변경 뒤에도 재생성되지 못했던 `telemetry.py`·`ui_capabilities.py` 모델을 정본대로
  다시 생성했다(point address `{building}` 세그먼트·`DataSource`·`PointKind`).

- 비식별 데모 건물은 기존 `BuildingIdentity`의
  `virtual_asset + provisional + unmatched` 조합으로 전달한다. 실제 건물의 25자리
  건물관리번호와 19자리 필지번호가 원본에서 비식별된 상태이며, 가상 건물을 만들었다는
  뜻도 공간 식별이 `not_applicable`이라는 뜻도 아니다. 번호를 임의 생성하지 않는다.

## v0.3.46 — 2026-08-26

### `household_consent` v1.2 — 보호는 동의보다 위에 있고, 준비 판정은 한 곳에서

두 축이 빠져 있었다.

- **`ProtectionState`** — 취약 거주자 보호. 동의와 **다른 축**이다: 동의는 "해도 되나",
  보호는 "해서는 안 되나". 가구가 동의했더라도 이 상태가 서 있으면 감축을 걸지 않고,
  **재동의로 풀리지 않는다**(명시적 해제만) — 그래서 권위다. ⚠ 제어 해제는 계속
  허용한다(보호는 제어를 놓지 못하게 하는 것이 아니다). ⚠ 필드 이름이 `vulnerable_*`
  가 아닌 이유: 사람을 분류하지 않고 **보호 조치**를 기록한다. `note` 에 건강 정보를
  적지 않는다.
- **`PreflightState` · `PreflightBlocker`** — *"지금 이 가구에 제안을 만들어도 되는가"*
  를 엣지가 한 번 판정해 **이름으로** 돌려준다. 화면이 동의·잔여 횟수·보호를 각각
  조회해 스스로 조합하면 그 규칙이 양쪽에 살고 언젠가 갈라진다. `max_setpoint_c` 를
  함께 주어 **화면이 넘겨 제안하지 못하게** 한다 — 넘겨 놓고 엣지가 자르면 승인 화면의
  숫자와 실제가 달라진다.

---

## v0.3.45 — 2026-08-26

### `household_consent` v1.1 — 설명만 필수였던 필드를 **실제로** 필수로

v0.3.44 의 `ConsentState` 는 `remaining_events_today` 와 `contract_version` 을 설명에서
"준다" 고 해 놓고 `required` 에 넣지 않았다. **엣지가 빠뜨려도 검증을 통과한다** — 계약이
아니라 희망이었다. 소비자가 붙기 전에 닫는다(v1.0 은 아무도 pin 하지 않았다).

- `ConsentState.required` += `remaining_events_today` · `contract_version`
- `ConsentState.requires_reconsent` 신설 — 정본 프리셋과 맞지 않는 **구 동의**를 들고
  있었다는 표시. ⚠ 숫자가 정본에 없다는 건 가구가 지금 표에 없는 범위에 동의했다는
  뜻이다. 그걸 가까운 프리셋으로 승격하면 **동의하지 않은 범위**를 적용하게 된다 —
  참여로 세지 않고 화면이 다시 묻게 한다.

---

## v0.3.44 — 2026-08-26

### `household_consent` 신설 — 화면이 보여준 숫자와 엣지가 거는 숫자를 한 표에서 읽는다

가정 DR 동의는 세 축(`max_setpoint_delta_c` · `max_duration_min` ·
`max_events_per_day`)을 갖는데, 화면(AIRO Home)은 목적별 동의만 받고 엣지(edge-agent)만
숫자를 알고 있었다. 각자 상수를 들면 **"보통" 의 뜻이 갈라지고**, 갈라진 뒤에는 어느
쪽이 진실인지 판정할 근거가 없다.

- **`household_consent`** — 프리셋 3 종 정본(`light` 1℃·120분·1회 / `standard`
  2℃·120분·2회 / `deep` 3℃·240분·3회) + `ConsentRequest`(PUT) · `ConsentState`(GET).
  기본 선택은 **없다** — 가구가 고르지 않으면 동의가 아니다.
- `ConsentRequest.displayed` — **가구에게 실제로 보여준 숫자**(선택). 보내면 수신자가
  정본과 대조해 다르면 거부한다. 화면이 "2℃" 라 말하고 엣지가 3℃ 를 거는 드리프트를
  계약 단계에서 잡는다.
- `ConsentState.remaining_events_today` — 소비자가 직접 빼서 쓰면 **날짜 롤오버 시점이
  어긋난다**(엣지는 넘어갔는데 화면은 어제 값으로 뺀다). 파생을 한 곳에서 한다.
- ⚠ **`control_command` 에는 아무것도 추가하지 않았다.** 명령 계약과 동의 계약은 별개
  축이다 — 명령에 동의 범위를 실으면 명령마다 동의가 재협상되는 꼴이 되고, 동의는
  명령보다 수명이 길다.
- 소비: `edge-agent`(PUT/GET 검증 + 프리셋 파생) · AIRO Home(선택지 표시·제안 제한).
  codegen: `HOUSEHOLD_CONSENT_PRESETS` · `_PRESET_IDS` · `_VERSION`.

---

## v0.3.40 — 2026-08-16

### `edge_strategy_capability` 신설 — 부를 수 있는 것과 **할 수 있는 것**을 가른다

화면은 전략 23 종을 전부 내주는데 엣지가 받는 건 9 종이었다. 격차 14 종이
**어디에도 적혀 있지 않았고**, 거부 메시지는 `"M00~M20 이어야 함"` 이라 실제 이유를
거짓으로 말했다(M01 은 그 범위 안인데도 거부된다). 제어 계통에서 이건 라벨 오류보다
위험하다 — **누를 수 있는 버튼이 아무 일도 안 하는 것**이다.

- **`edge_strategy_capability`** — `dispatchable` 9 종 + `not_dispatchable` 14 종
  (**사유 필수**). 정본(`ems_strategies`)의 부분집합임을 명시한다. 추가(additive)라
  기존 소비자를 깨지 않는다.
- 소비: `edge-agent`(`_VALID_STRATEGIES` 파생) · `gen_ops.py`(UI enum 파생) ·
  `tools/verify_strategy_dispatchability.py`(격차 감시).
- 스키마 33 종이 되며 `SOURCE_HASH` 가 `02246e19d4efcab2` → `e612a519bde61458` 로
  바뀐다. **소비자 전원 regen + pin bump 가 함께 가야 한다**(이 릴리스의 이유).

### 구값 스윕 범위를 소비 저장소에서 파생

스윕 대상이 6 개로 박혀 있었는데 생성 상수를 쓰는 저장소는 8 개였다 —
`building-energy-sejong`·`ingestion-worker`·`8sim-shared` 는 **감시 밖**이었다.
(실제 잔재는 0 건. 손해가 아니라 공백이었다.) 이제
`gen_constants.PROJECT_TARGETS` 에서 파생하고, 두 목록이 갈라지면 시험이 실패한다.

---

## v0.3.37 — 2026-08-03

### `simulation_channels` 신설 + `telemetry` v1.6 (설정온도 냉/난 분리)

시뮬 대조 19채널의 정본이 캠페인 `data_contract.py` 에만 있어, 소비단(MGCC)이
커버리지를 판정하려면 **손으로 베껴야 했다**(수동 미러).

- **`simulation_channels`** — Tier A 15 + Tier B 4. 핵심은 목록이 아니라
  **telemetry 대응 매핑**이다. `gap` 채널은 소비단이 "아직 안 온 것" 이 아니라
  **올 수 없는 것**으로 다뤄야 한다. `substitutable_externally` 로 외부 조달
  (기상청 ASOS)을 건물 결측과 가른다 — 안 가르면 외기계를 안 단 멀쩡한 건물이
  전부 대조 불가가 된다.
- **`telemetry` v1.6** — 채널 계약을 만들자 병목이 **딱 둘**로 드러났다
  (`hourly_setpoint_cool`·`_heat`). `hvac_setpoint_c` 가 하나뿐이라 냉/난을 가를 수
  없었다 — **계약의 공백이지 건물 탓이 아니다**. `hvac_setpoint_cool_c`/`_heat_c`
  신설(선택 필드, 기존 필드 유지).

⚠ 결과: **Tier A 15채널이 전부 확보 가능**해졌다(용도별 5 = v1.5 `end_use_meters`,
설정온도 2 = v1.6, 외기 3 = ASOS 대체). 남은 gap 3 은 전부 Tier B(결측 허용).
⚠ 캐스케이드 **0**.

---

## v0.3.36 — 2026-08-03

### `telemetry` v1.5 `end_use_meters[]` + `capability_tier` v1.1 (C3 관측 승격)

한국 BEMS 제도는 생산·저장·사용 에너지를 **에너지원별(전기/연료/열) × 5대 용도
(냉방·난방·급탕·조명·환기)** 로 요구하는데(구 별표 12 #3, ZEB 필수 #3), 이 축은
**Brick·Haystack·IFC 어디에도 없고** telemetry v1.4 에도 없었다 — 건물에서 올라오는
건 `power_kw` **총량 하나**뿐이었다.

- **`end_use_meters[]`**(선택) — 값집합은 `equipment_taxonomy` 의 `EnergySource`·
  `EndUse` 를 **그대로** 쓴다(설비 분류와 계량 보고가 다른 말을 쓰면 안 된다).
  ⚠ 총량과 **다른 축**이라 합이 총량과 맞아야 한다는 제약을 두지 않는다 — 계량
  경계가 달라 안 맞는 게 정상이고, 억지로 맞추면 배분값을 실계량처럼 보고하게 된다.
  ⚠ `estimated` 로 실계량과 배분·추정을 가른다.
- **`capability_tier` C3** `no_contract_channel` → **`observable`**. 이 등급이
  '관측 불가' 였던 건 건물 탓이 아니라 **계약의 공백**이었다.

⚠ 캐스케이드 **0**(둘 다 runtime-validate). 소비단(MGCC)이 C3 파생을 함께 구현한다 —
계약만 바꾸면 "관측 가능하다는데 아무도 관측 못 하는" 상태가 되고 C3 신고 건물이
전부 거짓 불일치로 뜬다.

---

## v0.3.35 — 2026-08-03

### `edge_registration` v1.4 — 설비 인벤토리 (요약 + 선택 전수)

건물 그룹 관제가 "이 건물에 무엇이 몇 대 있나" 를 물으면 답이 없었다. 설비 대장은
엣지 로컬(`DeviceCatalog`)에만 있고 원격으로 나올 길이 없었다.

- **`equipment_summary`** — 설비 종류 → 대수. `EquipmentKind` 키만 허용(수동 미러
  금지). 그룹 관제가 알아야 할 하한이 여기까지다
- **`equipment[]`** — 드릴다운용 요약 엔트리(선택). `device_id`·`kind`·`subtype`·
  `label`·`floor`·`zone`·`point_id`

⚠ **`driver_address` 는 싣지 않는다.** BACnet 인스턴스·Modbus 레지스터는 현장
바인딩 상세이고, 원격이 사본을 들고 있으면 현장이 배선을 바꿔도 **원격 사본만 낡은
채 남는다**(DECISION-POINT-ADDRESSING 의 축 분리: BACnet=바인딩 / CPA=식별).

⚠ 전수를 필수로 하지 않은 이유: 건물당 수백 개까지 가고 retained 등록 페이로드가
그만큼 커진다. **요약은 항상, 전수는 필요할 때.**

⚠ 캐스케이드 **0** (`_usage=runtime-validate`).

소비: MGCC 가 **엣지 로컬 대장과 자체 저작을 공존**시킨다(사용자 결정) —
`edge_local > mgcc` 우선순위로 합치되 충돌은 덮지 않고 지목한다.

---

## v0.3.34 — 2026-08-03

### `equipment_taxonomy` v1.2 — 설비 종류 7 신설 + 하위형·시뮬근거·용도축

E+ IDF 42본 전수 파싱 근거. 추가 기준은 이름이 아니라 **표준 점 집합이 달라지거나
제어 의미가 달라질 때**만이다.

- **`EquipmentKind` 13 → 20** — `radiant`(온돌 8본, 공급수온 제어 + 지연응답) ·
  `vrf`(9) · `district_heat`(6, 생산이 아니라 **구매**) · `dhw`(21 최다, 레지오넬라
  하한) · `refrigeration`(17, **식품안전 제약으로 DR 제외 대상**) ·
  `cooling_tower`(3) · `erv`(6, EMS M08 대상)
- **`point_sets` 12종 44점 → 19종 77점.** ⚠ 새 니모닉은 4개뿐(`CASE_T`·`DEFROST`·
  `EAT`·`WHEEL`) — 계통(공기/물)은 `kind` 가 말한다. 기존 chiller·boiler 가 이미 물
  계통에 SAT/RAT 을 쓰므로 SWT/RWT 를 새로 만들면 같은 개념이 두 이름을 갖는다.
  표준 앵커에 **`ifc` 추가**(전열교환기는 IFC 만 정확 — Haystack 은 점으로 표현)
- **`capability_matrix.refrigeration = []`** 은 의도다(원격 감축 대상 아님)
- **`subtypes`** — 종류를 늘리지 않고 실체를 남기는 축(표시·분류용, 제어 계약 아님)
- **`simulation_backed`** — 캠페인별(`{KR, GLOBAL}`) 4값. `unreported` 를 `none` 과
  나눈 게 핵심: none(ESS)은 모델 신설, unreported(PV)는 출력 2줄 추가 후 재실행이라
  **비용이 한 자릿수 다르다**. `pv` = KR:none / GLOBAL:unreported
- **`energy_end_use`** — 에너지원 × 5대 용도 교차축. Brick·Haystack·IFC 어디에도
  없다(국제 표준의 결함이 아니라 관할권 요구). ⚠ 「동력」은 5대 용도에 없다(정정)

### `provision` v1.5 — `selector.equipment_kind` 미러 동기화

guarded mirror 가드(`test_mirrored_vocabularies_match_their_source`)가 잡았다.
안 고쳤으면 점 설정 selector 로 `radiant`·`dhw` 를 지목하는 순간 **거부되면서
이유는 어디에도 안 나왔을** 것이다.

⚠ **캐스케이드 8 repo.** 델타는 순수 추가 — `EQUIPMENT_KINDS` +7 ·
`EQUIPMENT_CAPABILITIES` +7 · `SOURCE_HASH`. 기존 값 무변경.

---

## v0.3.33 — 2026-08-02

### `capability_tier` 신설 + `affiliations` 축 3종 — 능력이 부족한 건물을 담는 어휘

건물 그룹 EMS 에서 **BEMS 없이 월 청구서만 있는 건물**(지점·창고·임차층)을 어떻게
다룰지가 계약에 없었다. 소비자가 등급 문자열을 코드에 박으면 수동 미러가 되므로 EC 선행.

- **`capability_tier.json` v1.0** — 관측 `C0~C4` · 제어 `A0~A4` · `BaselineSource` 3값.
  세 축은 **직교**한다(C4/A0 임차 건물 · C1/A1 수동 건물 둘 다 실재) — 스칼라 하나로
  뭉개면 반드시 하나를 틀린다. 판정 증거는 **기존 계약만** 가리킨다(`telemetry.power_kw`·
  `zones[]` · `venue.kind` · `provision_ack` · `dispatch_ack`) — 새 어휘를 만들지 않았다.
  `kind=telemetry` 는 이미 있던 A0 였다.
  ⭐ **관측 불가를 관측 불가로 표기**: `C3`(용도별)은 telemetry v1.4 에 분해 채널이
  없어 `evidence.status=no_contract_channel` — declared 로만 가능하고 observed 로는
  도달할 수 없다고 계약이 스스로 밝힌다.
  `inclusion_rules` 7 + `participation_floor`(배분 C2 · 발령 A2 · 회계 C1).
- **`edge_registration` v1.2 → v1.3** — `affiliations[].type += dr_resource ·
  legal_entity · building`. 그룹 단위가 제도 축마다 다르다 — ZEB·BEMS설치확인은 동 1개,
  목표관리제는 법인/사업장, **수요자원 거래시장은 다수 수용가 묶음이 등록·정산 단위**다.
  배타성(microgrid/legal_entity/building 각 1개)과 저작 주체를 명시.

⚠ **캐스케이드 0** — 두 스키마 모두 `_usage=runtime-validate` 라 `load_schemas()` 대상이
아니다(`--all --check` = drift 0). 소비자 재생성·pin lockstep 불요. 비싼
`equipment_taxonomy` v1.2 는 의도적으로 분리했다 — 섞으면 값싼 잠금해제가 8-repo
lockstep 뒤에 줄을 선다.

---

## v0.3.32 — 2026-08-02

### codegen: `building-energy-sejong` 등록 + 아카이브 러너 인벤토리 정리

sejong 의 `_generated_constants.{py,ts}` 는 "AUTO-GENERATED … 재생성" 이라고
스스로 밝히면서 `PROJECT_TARGETS` 에 없었다 — **한 번 생성되고 고아**가 된 상태.
그 사이 M21·M22 승격(2026-07-10)을 놓쳤고 **배출계수도 0.4594 구값**으로 남아
CO₂ 를 잘못 계산했다(정본 0.4173). sejong 엔 CI 도 없어 1,618 시험이 있는데도
아무도 몰랐다.

⚠ **self-hash 캐스케이드**: `gen_constants.py` 는 스키마 + **자기 자신**을 해시한다
(위장 통과 방지, `_source_hash`). 따라서 PROJECT_TARGETS 를 건드리면 **전 소비자의
SOURCE_HASH 가 바뀐다** — 이 릴리스는 소비자 일괄 재생성을 동반한다.

- `PROJECT_TARGETS += building-energy-sejong` (python 44 심볼 / ts i18n 2종)
- `runners.expected.json` — 아카이브 repo 러너 3개 제거(reverse-ems,
  ems-transformer×2). 워크플로가 없어 잡이 오지 않는데 컨테이너만 상주했고,
  인벤토리에 남기면 중지가 "소멸"로 오탐된다.

---

## 이전 이력 (분할 보관)

v0.3.31 (2026-08-01) 이전 절 전부 — 0.3.18~0.3.31 · 0.3.5~0.3.8 · 0.2.0~0.2.3 · 0.1.0 · v1.0~v1.4.0 · (unversioned) 항목 — 는 원문 그대로 [docs/legacy/changelog/CHANGELOG_2026-04-19_to_2026-08-01.md](docs/legacy/changelog/CHANGELOG_2026-04-19_to_2026-08-01.md) 로 옮겼다 (2026-09-19 분할). 새 항목은 이 파일 맨 위에 추가한다.
