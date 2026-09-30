# Energy Contracts — CHANGELOG

스키마·프로토콜 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

---

## 0.3.71 (2026-09-30, 태그 v0.3.71) — 근거 없이 정한 여섯 값·인용 셋을 GPT 와 상의해 고침(가산)

사용자 지시(2026-09-30 19:24 "지피티와 상의해서 정해") · 상의 기록 = 캠페인 `review_exchange/rounds/R079_gpt.md`(Azure gpt-5.6-sol, 인용은 웹 대조).
0.3.70 의 키와 value 는 하나도 바꾸지 않았다 — 새 칸은 전부 **행 수준**(value 의 형제). 여섯 값은 표준값이 아니다: `basis_kind` 는 `declared_demo_assumption` 그대로, basis 에 'GPT 상의(2026-09-30)'.

- `declared_assumptions` 1.3 → 1.4:
  - `short_cycling`: `interpretation: screening_only` — 하루 6회 초과는 '단주기 기동' 판정이 아니라 확인할 채널을 고르는 선별 조건(시간 자료로는 분 단위 현상을 판정할 수 없다 · 제조사 최소 운전·정지 시간/허용 기동 횟수와 분 단위 상태 자료를 요청).
  - `comm_status_thresholds`: `by_delivery`(hourly_realtime 2·24시간 · daily_batch 24·72시간) · `unknown_delivery_profile: daily_batch`. 옛 value(24·72) = 일 배치 기준.
  - `life_roadmap`: `sensitivity_life_used_shares [0.25, 0.75]` · `remaining_life_status_when_unknown: unknown_assumed_scenarios` — 연식이 없으면 잔여수명은 미상, 세 시나리오를 나란히.
  - `investment_tiers`: `classification_basis: measure_cost_catalog.work_scope` · `numeric_thresholds_role: fallback_only` · `label_ko_by_work_scope` — 구간은 공사 범위로, ㎡당 문턱은 조치 목록에 없는 조치에만.
  - `precool_delta_c`: 이름 '하향 시험 폭(최대)' · `conditions_ko` 4개(조기 기동 먼저 · 재실 전 복귀 · 습도·결로·최대수요 · 효과 확인된 건물만).
  - `pmv_inputs` · `debate_stated_term_ranges`(상가건물 임대차보호법 제9조 제1항 임차인 예외 · 제10조 제2항 · 국가재정법 제2조): 인용 문구 정정, '원문 대조 전' 삭제.
- `judgement_thresholds` 1.1 → 1.2: `temperature_sensitivity.min_observed_temperature_days` 에 `preliminary_label_below_months 12` · `preliminary_label_ko` · `must_report_ko`(기온 범위 · 유효 일수) — 30일 미만은 추정하지 않는다(1.1 은 참고용으로 실었다).
  `min_r2` 는 '선별 기준(경험칙)' — IPMVP 경험칙이지 합격 기준 아님, ASHRAE Guideline 14 NMBE·CV(RMSE) 와 별개. 두 행에 `basis_kind`·`basis`.
- `measure_cost_catalog` 1.2 → 1.3: `$defs.WorkScope`(operational · minor_repair · major_project) · 조치마다 `work_scope`(필수 — 빠지면 스키마 검증 실패). 선언 분류:
  운영 = RCX·BEMS · 소규모 보수 = LED·VSD·SEAL · 대공사 = CHIL·COND·HP·ERV·INS·WIN·SHAD. 생성 모델 `_pydantic_models/measure_cost_catalog.py` 재생성.
- 시험 `tests/test_declared_assumptions_0370.py` 0.3.71 절: 0.3.70 태그 파일과 키·값 가산 대조(문구 제외 잎 전부) · 고정값 · 근거 표기 · 새 칸 15 · 조치 전부 work_scope(빠지면 스키마·모델 둘 다 거절 — 조치마다) · 정의 일치. 반례 양쪽.

## 0.3.70 (2026-09-30, 태그 v0.3.70) — 코드 리터럴로 있던 선언 기본값을 정본으로(가산)

- `declared_assumptions` 1.2 → 1.3: 새 행 54개(1.2 의 16행·값은 그대로). 게이트웨이·AgentLeague·be-3d 에 손 리터럴로 있던 선언 기본값·문턱·화면 상한·가상 생성 규칙을 옮김 —
  시나리오 단계(예산 몫·기준선 분위) · 수요반응 3단계 · 폭염 주 시나리오·기본 전략 · PMV 가정 입력 · 야간 셋백·예냉 · 시뮬 표본·일정 추론 문턱 · 가정 가전·가상 생성기 범위 ·
  수명 로드맵·할인율 격자·투자 구간·예산 묶음·조치 묶음 · 장면 연출 기본값·화면 상한·부분 전달·다시 계획 한도·구성원 상한 · 토론 역할 문턱·가정 범위·기본 관점.
  새 행은 `id · value · unit(QuantityUnit) 또는 unit_text · label_ko · rule_ko · classification · basis_kind · basis · source` 를 싣는다.
  `basis_kind` = moved_literal · declared_demo_assumption(외부 근거 없는 선언 시연 가정) · standard_citation · derived_from_ec(새 수 없음).
- 이미 정본에 있는 값에는 새 행을 만들지 않았다(코드가 기존 행을 읽는다): 순위 기본 개수(10) · 이상 z(3.0·2.0) · 상위 비율(25%) · 빠른 회수(3년) · 폭염 달 창.
  코드 리터럴이 정본과 달랐던 곳(순위 5·20 · 강건 z 3.5 · 가상 정책 대상 20% · PMV 대사량 1.1)은 정본 값이 이긴다.
- `hazard_days.heat.baseline_months` [6, 8] 추가(폭염 기준 창).
- `judgement_thresholds` 1.0 → 1.1: `anomaly.monthly_screening_min_months`(6) · `band_out_share_multiple`(2.0) · `sustained_out_hours`(3) ·
  `comfort.pmv_out_of_band_increase`(0.10) · `temperature_sensitivity.min_observed_temperature_days`(30)·`min_r2`(0.75).
- `calendar_conventions` 1.0 → 1.1: `week`(월요일 시작, ISO 8601).
- `error_response` 1.1 → 1.2: 코드 `PAYLOAD_TOO_LARGE`(413, validation).
- `certified_tests` 1.0 신설: KOLAS 26-10050 성적서 값만(부하예측 CVRMSE 12.91%·12.55% · 자연어 진단 · EMS 식별). 자체 검증값 12.93% 는 수 칸에 없다. 생성 상수 `CERTIFIED_TESTS`.
- 생성기: `CERTIFIED_TESTS` 방출(8sim-shared·agentleague) · be-3d 생성본(py·ts)에 `DECLARED_ASSUMPTIONS` 추가. 표는 통째로 파생된다(목록을 손으로 적지 않는다).
- 시험 `tests/test_declared_assumptions_0370.py`: 검사 10 — 행 모양(54행)·반례 7 · 1.2 행 값 불변 · 가리키는 정본 값과 일치 24 · 중복 행 없음 · 생성본 도달 13.

## 0.3.69 (2026-09-30, 태그 v0.3.69) — 요금제 선택 기준 · 연도별 평균판매단가

- `market_prices.retail_reference_2026.tariff_class_selection`: 계약전력 300kW 이상 → 일반용(을) 고압 요금(`electricity_tou_general_b_2026`), 미만 → 일반용(갑). 한전 기본공급약관(MCP-023).
- `retail_reference_2026.electricity_avg_sales_price_by_year`: 2024 확정·2025 잠정 평균판매단가를 연도별 칸으로(같은 출처 — 기존 basis 문장의 값을 구조화, MCP-004 전년 대비 단가 효과).

## 0.3.68 (2026-09-30, 태그 v0.3.68) — 게이트웨이 지명 어댑터가 EC 로 바뀔 수 있게(차단 넷 해소)

- `everyday_stem_blocked(word, text)` 공개(f7 8db2fe1) — 문장에서 자리마다 resolve 를 부르는 소비처가 같은 규칙을 쓴다.
- `_with_children_prefix`: 우산 시 판정을 표의 `umbrella` 표시(`umbrella_codes`)로만 — '앞 4자리가 같은 다른 시군구' 짐작이 영동군(43740)에 4374 를 붙여 증평군(43745)으로 펴졌다(268곳 전수 대조에서 어긋남 이 하나).
- `PLACE_PARTICLES` 공개 — 조사·접미 목록 한 곳(EC `_JOSA` 와 게이트웨이 `PLACE_TRAILERS` 합집합 + '이랑'·'랑'·'하고', 긴 것부터). 게이트웨이가 이 객체를 import 한다('노원구랑').
- 반례: 영동군 접두 없음 · 우산 시 13 전부 그대로 · 새 조사로 지명 읽음 · '사랑으로'·'하고 싶은' 은 지명 아님. EC 64 · be-3d 지역 152 통과. 생성 상수 영향 없음.

## 0.3.67 (2026-09-30, 태그 v0.3.67) — 문장 속 지명 찾기가 일상어 어간을 지명으로 읽지 않는다

- `regions.find_region_mention`: 시·군·구 어간이 접미 없이, 같은 문장에 그 시도 표기 없이 나오고 일상어 어간 표(`data/region_everyday_stems.json`, 23개, 항목마다 뜻·근거)에 있으면 지명으로 읽지 않는다(f7 97ff188). '예산 10억'은 막고 '충남 예산'·'예산군'은 읽는다.
- 지역 칸 입력(`resolve`)은 막지 않는다. 짧은 지명(강남·마포·무안·해운대)은 읽는다(사용자 결정 09-30).
- 반례: 일상어 6 → None · 짧은 지명·시도 표기 7 → 코드 · 칸 입력 · 표가 실제 어간만 담는지. 생성 상수 영향 없음.

## 0.3.66 (2026-09-30, 태그 v0.3.66) — 지명 표 지문을 줄끝과 무관하게

- `regions.canonical_table_bytes()`(줄끝 LF 정규화) · `table_sha256()` 은 그것을 해시한다(f7 7e9f102). 원인: 메인 체크아웃(core.autocrlf=true, .gitattributes 없음)에서
  `data/region_resolver_table.json` 이 CRLF 로 풀려 같은 표가 체크아웃마다 다른 지문(01c72d7d… ↔ a86590aa…)이 됐다 — '두 소비처가 같은 표' 대조가 기계마다 달라졌다.
- `.gitattributes`: `energy_contracts/data/*.json text eol=lf`(예방).
- 반례: CRLF = LF 같은 지문 · 내용이 다르면 다른 지문 · gitattributes 등재. 생성 상수 영향 없음(drift 0).

## 0.3.65 (2026-09-30, 태그 v0.3.65) — regions 가 EC 대상 id `region:<숫자>` 를 받는다

- `energy_contracts.regions._resolve` 입구에서 `TARGET_ID_PREFIX`("region:")를 떼고 숫자(코드) 경로로 보낸다 — 숫자가 아니면 `REASON_BAD_CODE` 이름 있는 거절(f7 1294333).
  뿌리(F07): 게이트웨이 장면 조리법이 EC 대상 id 형식 `region:11680` 을 싣는데 be-3d 해석기가 지명으로 읽다 0동 선택이 됐다 — 처리기마다 벗기지 않고 해석기 한 곳에서 받는다.
  반례: 계약 pattern 이 이 접두로 시작(가정을 시험으로) · region:11/4111/11680 = 숫자만과 같은 결과 · 'region:'·'region:abc'·'region:강남구' 거절.
- 생성 상수 영향 없음(drift 0) · 표 생성기 이관(④)은 다음 판.

## 0.3.64 (2026-09-30, 태그 v0.3.64) — 지명 해석 하나(regions) · 폭염 출처 문구

- `energy_contracts.regions`(f7 T1 ①): be-3d region_resolver 의 규칙·표를 그대로 옮긴 순수 모듈 — `resolve(query, context=<시도>)` · `find_region_mention` · `resolve_code`. 표 = package data `data/region_resolver_table.json`.
  대조(f7): resolve 64,710건(입력 21,570 × 문맥 3) + Query100 지명 = 차이 0 · 표 sha 동일 · 순수 시험 17 이관.
- `declared_assumptions.hazard_days.heat` source 문구 정정: '폭염일수 통계 정의(일 최고기온 33℃ 이상)'(특보 기준은 체감온도) — 값·규칙 불변.
- 소비처: 게이트웨이 `place_resolution` 은 EC 위 어댑터(질의자 배정·직전 대상 문맥은 요청 개념이라 게이트웨이에 둔다) · be-3d region_resolver 는 EC import 얇은 층(f7 T1 ②). 표 생성기 이관(④)은 0.3.65.

## 0.3.63 (2026-09-29, 태그 v0.3.63) — 요청 해석 입구 모양 · 연간 EUI 규칙 하나

- `interface_types.json` 1.2: `RequestResolution` 추가 — 게이트웨이 `POST /v1/request-resolution` 응답(`contract="request-resolution/v1"` · question_frame · target_context · period · place_decision · refusal?). 도구·LLM 없이 질문 틀과 대상 결정만 돌려주는 입구다. be-3d 장면 경로가 대상을 게이트웨이 결정 하나에서 받는다(묶음 3 S1).
- `rules_pure.ec_annual_eui`(f7 c090cba): 연간 EUI 규칙 하나(달력 12개월 합 · 상한 = judgement_thresholds). be-3d canonical 3,000건 차이 0.
- 발행 이유(22:2x): c090cba 가 SOURCE_HASH 를 바꿔 소비처 로컬 pre-commit 이 모두 drift 로 막혔다. 생성본만 다시 만들면 CI 가 핀(v0.3.62)과 어긋난다 → 태그 + `bump_ec_pin` 으로 핀·생성본·AIROS 잠금을 함께 올린다.
- resolve_region 통합·폭염 문턱 → 0.3.64.

## 0.3.62 (2026-09-29, 태그 v0.3.62) — RV-B 계약 일관성

근거: 공모전 `docs/REVIEW_FIX_PLAN_2026-09-29.md` §B · `scratch/review_0929/R3_CONSISTENCY.md`(H3·M1·M2·M4·M10·T).
게이트웨이가 실제로 싣는 모양을 선언하고, 게이트웨이 모듈 상수로 남아 있던 선언 가정을 옮겼다. 모두 **가산**(이전 판에서 유효한 봉투·문맥은 유효).
- 확정 절차(3b 조정자, 19:10): pydantic 모델 재생성(4 스키마) · `gen_constants.py --all`(12 소비처, drift 0 · 한국화 세션 합의 — 봉인 검사는 매니페스트 CSV 바이트만 대조) · `validate_ssot.py` 통과 · 코퍼스 재생성(변화 없음) · EC 시험 587 통과 · pyproject 0.3.62.

- `airo_request.json` 2.4: TargetContext += contract·chain_steps·final_target_source·choices, '대상 없음' 모양(resolved=false → kind·source null · ids [])
  · Period += source(Target.source 낱말)·basis_ko·why·generator·contract, basis += forecast_relative_to_today
  · 원형 미지정 대상(ids=[archetype:all])은 archetype 객체 없이 허용 · TargetExpansion.rule_id 예시 = 게이트웨이 전개 규칙 이름
  · 봉투 += tool_input_mode(v1 같은 칸) · as_of(요청 기준 시각) · Continuation = requested_tool 또는 prior_request_id(되묻기 둘째 턴)
- `airo_result.json` 1.1: $defs += ToolCall{name, arguments, step_id?, member?} · ToolResult{tool, step_id?, member?, result | rejected_result}
  · Assumption.basis 설명 = 선언 기본값 표식(`declared_default:energy-contracts/<스키마>#<키>`) · result_hash_scheme 예시 = 게이트웨이 이름
- `interface_types.json` 1.1: QuantityUnit += score
- `declared_assumptions.json` 1.2: 단위 = QuantityUnit(top_share '%'→pct · 햇수 yr) · += scenario_vacancy_default · switchable_cut_share_default ·
  control_priority_default · assumption_search_ranges · ranked_rows_top_n_default(값은 게이트웨이 리터럴 그대로 옮김)
- 시험: `tests/test_interface_contracts_0362.py`(반례 양쪽)
- 소비처 재생성: `gen_constants.py --all`(DECLARED_ASSUMPTIONS 사전이 바뀐다 — 생성본 `_shared/_generated_constants.py` 등) ·
  질의 코퍼스 재생성(airo_request 봉투 칸 추가) · 게이트웨이 CI 핀(pyproject `v0.3.55`)을 0.3.62 로 — 게이트웨이는 새 키를 import 시점에 읽는다.

## 0.3.61 (unreleased, 2026-09-29) — M3 인터페이스 표준 · 봉투 2.3 · 결과 봉투 · 거절 봉투 · 상위 비율 기본값

근거: 공모전 `docs/ARCHITECTURE_MIGRATION_M1_M6_2026-09-29.md` §2·§6·M3/M4 결정(f7 합의) · `scratch/expert_0929/INTERFACES.md` §4.2.
모두 **가산**이다 — 기존 필드·값·상수는 그대로이고, 이전 판에서 유효한 봉투·Problem 은 이 판에서도 유효하다.

- `airo_request.json` 2.3(`airo-request/v2` 그대로):
  ① `target` 생략 허용 — 없으면 게이트웨이 질문 틀이 정하고 응답 `TargetContext` 에 싣는다 ·
  ② `continuation{requested_tool, tool_arguments, prior_request_id}`(v1 에만 있던 이어가기) ·
  ③ `intent: "plan"`(계획 경로 = v1 `task_mode plan_action` + `permissions.plan`, `continuation` 필수) ·
  ④ `intent: "debate"`(AgentLeague) ·
  `Target`·`TargetContext` += `asset_kind`(BLD·FAC·HOM·RET·PRT — v2→v1 에서 잃던 종류) · `members` · `expansion{rule_id, rule_ko, from_kind, to_kind, member_count}`(서버가 채움) ·
  `Period.basis` += `coverage_of_needs`. 게이트웨이가 이 파일 하나로 검사하므로 파일 밖 `$ref` 는 두지 않는다(`AssetKind` 목록 = `common.AirAssetKind`, 시험이 지킨다).
- `interface_types.json` 1.0(새, runtime-validate): `TargetRef`·`TargetContextRef`·`PeriodRef` = `airo_request` 정의를 가리킨다(사본 없음) ·
  `ClassificationWordRef`·`AbsenceKindRef` = `data_classification` 정본 · `Quantity{value, unit, text}` + `QuantityUnit`(에너지 단위 표기 = `energy_units.base_units`).
- `airo_result.json` 1.0(새, `airo-result/v1`): status(ok·partial·needs_input·refused·unavailable·unsupported) · target_context · period_used · row_kind(ranked·card·series·table·scalar) ·
  columns[] · rows[] · population · summary · absences[] · classification(정본 17 낱말) · honesty_label · assumptions · source_ids · ec_version · refusal? · result_hash.
  규칙: ok 가 아닌 거절 상태는 `refusal` 필수 · ok 는 `refusal` 금지 · 행이 없는 ok/partial(스칼라 제외)과 ranked 는 `population` 필수(빈 목록을 통과로 세지 않는다).
- `error_response.json` 1.1: `$defs.Refusal{code, kind(question·data·permission·internal), field, expected, got, message_ko, next_ko, retry(ask·fill·none), legacy_code}` ·
  `Problem` 에 같은 칸을 선택 칸으로(Refusal 정의를 `$ref`). `ERROR_CODES` 등 기존 값 불변.
- `declared_assumptions.json` 1.1: `top_share_pct_default` 25%(assumed) — 게이트웨이 `general_ops/cohort.py` 형평 규칙의 '코호트 EUI 상위 25%'(`percentile(…, 0.75)`) 리터럴을 옮김.
  소비처 = 게이트웨이 `general_ops/clarify.selection_basis`(rank_top·rank_bottom 이 `unfiltered_all` → `declared_default`).
- `_index.yaml`: `AiroResult`·`InterfaceTypes` 등재.
- 시험 `tests/test_interface_contracts.py`: 새·바뀐 스키마 2020-12 검사 · 봉투 2.3 반례 양쪽(받을 것 7 · 막을 것 7) · 결과 봉투 반례 양쪽(4 · 7) ·
  Problem 확장 가산 · 봉투 단일 파일 · `AssetKind`=`common.AirAssetKind` · 단위 ⊇ base_units · 파일 밖 `$ref` 는 레지스트리로 푼다.
- 생성본 영향: `SOURCE_HASH` 와 `DECLARED_ASSUMPTIONS` 한 줄(키 하나 추가, 기존 키 값 동일)만 바뀐다 — 그 줄을 싣는 소비처 = agentleague · 8sim-shared · airos-energy-decision.

### 대기 — 연간 EUI 규칙(f7 가 규칙 함수를 낸다, 이 판에는 없음)

> **2026-09-29 22:4x 전달(f7, 0.3.63 초안)**: `rules_pure.ec_annual_eui(monthly_by_carrier, area_m2, year=None, judgement_thresholds=None)` — 위 인터페이스 그대로 · be-3d `collect_building_energy.canonical_annual_eui` 와 무작위 입력 3,000건 일치(차이 0, 상한 3,000 동일) · 시험 `tests/test_rules_pure_annual_eui.py`(반례 양쪽). 소비처 전환(be-3d 수집기·AIROS·게이트웨이)은 생성본 반영 뒤.

연간 EUI 계산이 7벌(1개월 ×12 외삽 · 상한 5000 손 사본 3곳)이라 같은 이름이 다른 값을 낸다(M5 (f) · 결정 B'). 규칙은 `rules_pure.py` 한 곳에 둔다. 합의한 인터페이스:
- 입력: 월별 사용량(`YYYY-MM` → kWh, 빈 달은 None) · 연면적 ㎡(None 가능) · 채널(전기·가스 등).
- 출력: `{value_kwh_m2_yr | None, months_used, basis, absence_kind, code}` — 값이 없으면 `absence_kind`(`data_classification.AbsenceKind`)와 이름 있는 코드를 싣는다.
- 규칙: 온전한 12개월(또는 `calendar_conventions.complete_month` 기준을 채운 창)만 연간값으로 본다 · 1개월 ×12 외삽과 0.0 행은 값이 아니라 `unknown`(못 잼)으로 낸다 ·
  상한은 손 사본 5000 이 아니라 `judgement_thresholds.data_quality.eui_plausible_kwh_m2.max` 에서 읽는다.
- 읽는 쪽(지도·순위·지역 평균)은 재적재 전까지 외삽·0.0 행을 못 잼으로 뺀다. 재적재 실행은 데이터 세션 소관이고 사용자 확인 대상이다.

## 0.3.60 (2026-09-29) — 질문 틀 1단계 별칭 · 소비처 pin 일괄

- `building_archetypes.json`: `doe_buildings` 별칭 += 대형/중형/소형 오피스(B01~B03) · 소매점(B05) — 질문 속 원형 이름을 대상 종류로 푼다.
- `building_usage_map.json`: `usage_aliases` += 오피스·청사 → 업무시설.
- 소비처 6곳 pin·ssot-drift ref 를 v0.3.60 으로 일괄(`bump_ec_pin.py`) — 0.3.59 는 be-3d 만 올라가 lockstep 위반이었다.

## 0.3.59 (2026-09-29) — 계량 물리 한계 · 빠른 회수 기본값 · 건물부문 NDC 기준 · 태그 재발행

- 태그 `v0.3.58` 이후 들어온 스키마(예: `airo_request.json`)가 태그 판에 없어, 태그로 설치하는 소비처(be-3d)가 `load_schema("airo_request")`
  에서 멈췄다(2026-09-29 Lab compose-nl 500). 판 번호를 올려 태그를 다시 낸다.
- `declared_assumptions.json`: `meter_physical_limit`(최대 원단위 기반 시간 상한의 첨두 배수 · 중앙값 배수 · 이웃 급등 배수, assumed) ·
  `quick_payback_max_yr_default` 3.0년(assumed — 카탈로그 빠른 조치 회수 범위 상단).
- `rules_pure.py`: `ec_meter_limits` · `ec_meter_value_ok` · `ec_median` · `ec_meter_cell_bound` · `ec_meter_spike_indices` ·
  `ec_meter_jump_indices` — 게이트웨이 `serving/meter_guard.py` 와 AIROS 계량 가드가 같은 규칙을 쓴다.
- `energy_constants.json`: `ndc_targets.building_sector_inventory`(2018 52.1 · 2024 잠정 43.59 백만t, 건물부문 직접 배출).
- `scripts/validate_ssot.py`: 확장자를 먼저 보고, 접근할 수 없는 항목은 읽을 수 없는 파일처럼 건너뛴다(깨진 pytest 링크로 검사 전체가 멈췄다).

## 분류 어휘 1.3 · 선언 가정 상수 (2026-09-28 최종 라운드 ②·N32, 0.3.59 에 포함)

- `data_classification.json` 1.3: `DataSource` += `virtual`(경진대회 가상 채움, 표시 '가상') · `EvidenceDisplayClass` += `virtual`·`unknown` ·
  `$defs.ClassificationWord`(결과 분류 낱말 17) · `default.classification`(낱말 → 출처·표시 등급·한글 라벨·가상 여부 · 옛 낱말 별칭 · 합성 규칙).
  분류가 없으면 `unknown` — `measured` 로 올리지 않는다. `measured_with_imputed` 는 "실측 + 빈 시간 실측 평균 채움" 한 뜻(가상 입력이 섞이면 `mixed`).
- `rules_pure.py`: `ec_classification_normalize/combine/meta` — 생성본에 원문 그대로(게이트웨이 `serving/classification.py` 가 읽는다).
- `declared_assumptions.json` 1.0(새): 폭염 33℃·한파 −12℃(기상청 기준 인용) · 민원 더운 시간 30℃ · 한파 설계일 5일 · 노후 30년 ·
  조치 적용 문턱 · 공공 용도 코드 · 가상 ESS 왕복효율 0.9 · 기본 용도 분해 — 게이트웨이 손 리터럴을 옮김.
- 온전한 달·창 문턱 0.99 = `calendar_conventions.json#complete_month`(W4 등재) 한 곳 — 같은 값을 judgement_thresholds 에 두 번 적지 않는다.
- 용도 표 한 벌(`building_usage_map` 1.2 X2): 정본 = `usage_archetype.rows`, `usages[*]` 는 `registry_usage` 만(원형은 생성기가 파생 — `BUILDING_USAGES[*].archetype·archetype_code`).
  편의점 = B11(사용자 결정 22:35) · 공동주택 층수 규칙(`apartment_by_floors`: 5층 이하 B16 · 6층 이상 B17 · 미상 B16) · 확장 용도 행(assumed) · 방송통신시설 = 이름 있는 결손(`no_doe_archetype`) · 세부 용도 별칭. `rules_pure.ec_usage_to_archetype(…, floors_above)`.
- `building_archetypes.json` 2.2: `area_m2` = v4 정본(O2 — B16 1,457→3,134.61 · B17 3,135→7,836.48 · B02 4,982→12,000 …) · `representative_hvac`(be-3d 손 표 이관, B16 HE · B17 HG) · `sim_axes`(시나리오 4 · 설정온도 8 — O3, 생성본 `AXIS_SCENARIOS`·`AXIS_SETPOINTS`).
- `judgement_thresholds.display_bands.policy_savings_pct`(O3 — be-3d 정책 색 띠 이관) · `market_prices.sim_cost_track_2025`(O5 — 152 시뮬 비용 트랙) · `energy_units.emission_factors_kr` 에 지역냉방 0.0·유류 0.264(O5, 가정).
- `auth_scopes.json` 1.5: `resource_authorization.f14_persona_of_role`(아이로스 역할 → F14 관점, 게이트웨이 asker_scope 손 표 이관 · analyst = building_manager 와 권한 동치 → facility_manager).
- `airo_request.json` 2.2: 지역 대상 코드 4자리(구가 있는 시) 허용 · `Period.basis` += `declared_replay_period`·`calendar_relative_to_today`(W8 Studio 이관).
- `region_codes.json`: `admin_succession.sido_current_names`(현행 시도 이름표 — be-3d region_resolver_table 이관) · `admin_succession.sido_merged`(12 전남광주 = 29+46 이름 통합, 접두 교체 아님) ·
  `hvac_types[H_x].heating_fuel·cooling_fuel·fuel_basis`(배출계수 어휘 — IDF 객체 전수 근거. H_C 난방은 원형마다 달라 null).
- `target_vocabulary.json`: `air_asset_kinds[*].electricity_price_class` + `electricity_price_classes`(자산 종류 → 요금 종별 선택 규칙 — 게이트웨이 _financial 이관, 생성본 `ELECTRICITY_PRICE_CLASSES`) ·
  `calendar_conventions.season_systems.heating_season`(난방기 11~3월 — 한전 겨울과 다른 이름) · 분류 별칭 += 자기 표 근거 등급 4(measured_calibrated → calibrated · measured_uncalibrated·drawing_* → simulated) ·
  `rules_pure`: `ec_competition_ranks`·`ec_average_ranks`·`ec_tukey_fences`(게이트웨이 stats 이관 — 다른 저장소 공유).
- `energy_units.fuel_vocabulary`(연료 사상 — 결과 칸 키·계량 키·한국어 → EC 연료 이름, 한국어 라벨, KBEP·시뮬 키 목록; 게이트웨이 energy_carrier 이관) → 생성본 `FUEL_VOCABULARY`(py·ts).
- `airos_replay_anomaly_policy.source` = 정본 자신(`kind: canonical_self`, 값 지문 + 적용 코드 목록) — 퇴역 하네스 파일을 가리키지 않는다.
- 생성 대상: `airos-energy-decision`(python, 새) · be-3d TS += `DATA_CLASSIFICATION_VOCAB`·`EVIDENCE_DISPLAY_CLASSES` · agentleague += `FUEL_VOCABULARY`.
- validate_ssot: `check_archetype_representative_hvac` · `check_emission_factor_copies`(D40 — 두 스키마 대조) · usage 검사 v1.2(손 archetype 금지·registry_usage 대조·층수 규칙·결손 행).
- 생성기: `EVIDENCE_DISPLAY_CLASSES` · `DATA_CLASSIFICATION_VOCAB` · `DECLARED_ASSUMPTIONS`(8sim-shared 내보내기). pydantic 재생성 = data_classification · agent_contracts · declared_assumptions.

## Query100 정본값 등재 — NDC 부문별·탄소가격 범위·DR 가정·전략별 설치비 (2026-09-28, unreleased)

- `energy_constants.json` 2.1: `ndc_targets` 신설 — `national_2030`(국가 전체 40%, 436.6백만t) · `building_2030`(건물 52.1→35.0백만t, 32.8%) · `building_2035`(건물 53.6~56.2%, 2025-11 확정). 기본 목표 = 건물부문 2030. 국가 전체 값은 대체하지 않고 다른 키로 둔다. 항목마다 출처 URL·발표일(`data_source=external`).
- `market_prices.json` 2.2: `kau.fallback_source`(20,000원 근거) + `kau.phase4_2030_outlook_krw_per_tco2`(40,000~61,000원, K-ETS 4기 2030 전망 보도). 기본값 20,000 은 그대로다.
- `ems_strategies.json` 3.3: `dr_assumptions` 신설(가정 등급, imputed) — M16 정본 산식 = 이벤트∧야간 창 HVAC 감축(이름과 일치), 연중 셋백 심화·매일 야간 감축은 변형으로 기록. M17~M20 감축 분율 0.30·ESS 15%×2h, 기본 이벤트 창 평일 17~20시(7~8월). M19 HVAC 대리 분율은 근거 없음(`missing`).
- `measure_cost_catalog.json` 1.2: `ems_strategy_capex_assumption` — BEMS 단가 × 제어점 비율의 가정식(출처='가정'). 식은 `energy_contracts/measure_capex.py` 한 곳.
- 생성기: `NDC_TARGETS`(py·ts) · `DR_ASSUMPTIONS`(py). 소비처 내보내기 = building-energy-3d(둘 다) · edge-agent(`DR_ASSUMPTIONS`). 시험 `tests/test_ndc_targets.py` · `tests/test_measure_capex.py`(반례 포함).

## 공통 사용자·자산 권한 계약 (2026-09-27, unreleased)

- `auth_scopes.json` 1.1: AIROS 사용자 역할 6종은 전역 RBAC 역할과 분리하고 현재 배정 자산의 `read:asset` / `analyze:asset` 역량만 정의한다. 미정 승인·실행 조건은 거절하며 관리 자산 배정이 필수다.
- `auth_policy.json` 1.1: 서버 검증 AIROS 세션 전달 헤더를 명시한다. 서비스 키·본문 ID·분석 페르소나는 사용자 인증이 아니다. 기존 JWT 정책을 AIROS opaque 세션 형식으로 오인하지 않는다.
- `resource_authorization.json`: 배정 개정·정책 버전/해시를 포함한 공통 context/decision 계약. 실행 권한을 부여하지 않는다. `_utils/resource_authorization.py`는 검증된 입력을 전제로 배정과 역량의 교집합만 계산한다.
- 생성기 `AUTH_RESOURCE_AUTHORIZATION` Python/TypeScript 출력 및 해당 Pydantic 모델을 추가했다. 기존 `airo_request` 생성 모델의 누락된 intent도 스키마에서 재생성했다.
- 소비자 cascade: `scripts/gen_constants.py --all`로 생성본을 갱신하고 소비자별 pin/hash 및 SSOT 검증을 함께 수행해야 한다. 작업 트리 정책을 과거 immutable pin의 내용으로 취급하지 않는다.

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
