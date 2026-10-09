# Energy Contracts — CHANGELOG

스키마·프로토콜 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

---

## 0.3.98 (2026-10-09, 태그 v0.3.98) — 일상어 동 어간 · 생성본 사본 점검

- `region_everyday_stems.json` 에 `dong_stems`(법정동 어간 중 일상어 — '가정') + `regions.everyday_dong_stem_blocked`: 같은 문장에 그 동의 시도·시군구 표기가 없으면 지명으로 읽지 않는다(GPT 901 재검증 AL-076~085).
- `gen_constants.py`: 8.simulation 거울(mpc_model/mpc_shared) 대상 등록 · `--check` 가 작업 공간의 미등록 생성본 사본을 UNREGISTERED 로 잡는다.

## 0.3.97 (2026-10-07, 태그 v0.3.97) — 연산 매니페스트 보정

- `scenario_versions/nature_compare` 가 실제로 저장하며 자료 기준월 칸이 생겨 default_period not_applicable→tool_rule(가산·핀만).

## 0.3.96 (2026-10-07, 태그 v0.3.96) — 연산 매니페스트 보정

- `operation_manifest` 재생성(가산 — 생성 상수·SOURCE_HASH 변경 없음, 핀만). 전제 해결·저장 산출물 선언 반영.

## 0.3.95 (2026-10-07, 태그 v0.3.95) — 연산 매니페스트 한정어 보정

- `operation_manifest` 재생성: 한정어 `qualifier:metric:gas`·`qualifier:metric:peak` 추가(가산 — 생성 상수·SOURCE_HASH 변경 없음, 핀만).

## 0.3.94 (2026-10-07, 태그 v0.3.94) — 연산 매니페스트: answer_reshape 2연산 · 전국 이야기 투어

- `operation_manifest` 재생성(448→450): `answer_reshape/decision_readiness`(바로 결정·추가 검토 나누기) · `answer_reshape/key_numbers`(핵심 숫자 N + 한 줄 주석) 추가 · `building_story_tour` subject_kinds 에 national · `sim_variant_compare/pack_variants` produces 보정. 가산 — 생성 상수·SOURCE_HASH 변경 없음(핀만).

## 0.3.93 (2026-10-07, 태그 v0.3.93) — 연산 매니페스트: 용도 거르기 한정어

- `operation_manifest` 재생성: 코호트 연산 항목에 `qualifier:usage_filter` 추가(질문이 말한 용도 이름을 정본 용도 코드로 거르는 한정어 — 게이트웨이 `cohort.question_use_filters`). 가산 — 생성 상수·SOURCE_HASH 변경 없음(핀만 올림).

## 0.3.92 (2026-10-06, 태그 v0.3.92) — 달력 규약 school_vacation · 연산 매니페스트 새 연산 둘

- `calendar_conventions.season_systems.school_vacation`(학교 방학 달 대표 가정 1·2·7·8월, classification assumed) — '방학' 질문의 기본 달(게이트웨이 question_frame.vacation_months). `CALENDAR_CONVENTIONS` 생성 상수가 바뀐다 — SOURCE_HASH 변경 · 소비처 재생성 필요.
- `operation_manifest` 재생성: `action_cross_compare`(여러 건물 같은 조치 비교) · `measured_store_analysis/event_day_plan`(행사 전·중·후 계획) 항목 추가, `simulation_pack_analysis/coldwave_heating_check`·`store_operations_brief/temp_rise_flat_power` produces 개념 추가(가산).

## 0.3.91 (2026-10-06, 태그 v0.3.91) — declared_assumptions 1.7: 새 행 셋(가산 · 생성 상수 바뀜)

- `capex_quote_band`(설치비 견적 편차 0.8~1.2 — 게이트웨이 리터럴을 옮김) · `map_estimate_fill_rule`(be-3d 지도 빈 값 채움 순서·문턱 20 — 게이트웨이 사본 제거, be-3d·게이트웨이가 같은 행을 읽음) · `role_tour_representative_quantile`(0.25 — 선언 시연 가정).
- 1.6 의 키와 값은 바꾸지 않았다. `DECLARED_ASSUMPTIONS` 생성 상수에 행이 더해져 SOURCE_HASH 가 바뀐다 — 소비처 재생성 필요.

## 0.3.90 (2026-10-06, 태그 v0.3.90) — 연산 매니페스트: scenario_versions/nature_compare

- 추가: `scenario_versions/nature_compare`(가상 예시 판 ↔ 실측 연결 판의 성격 비교 — 질문 낱말로 미리보기·차이를 가로채던 갈래를 명시 동작으로).
- `scenario_versions/diff` 의 파생 지표에서 원단위가 빠짐(그 갈래가 nature_compare 로 옮겨감) — 값 변경 없음.

## 0.3.89 (2026-10-06, 태그 v0.3.89) — 연산 매니페스트 파생 재생성(가산)

- `scenario_versions/diff·list·preview`: 저장된 판이 없을 때의 기본 결과 칸(지역 지도 기본 분석)으로 연도 축·원단위 지표가 파생에 더해짐.
- 연산 추가·제거·값 변경 없음.

## 0.3.88 (2026-10-06, 태그 v0.3.88) — 연산 매니페스트: 새 연산 다섯 (가산)

- 추가: `answer_reshape/measure_pair`(같은 건물 집합에 두 대책 · 같은 기준안) · `archetype_climate_grid/tradeoffs`(에너지·탄소·쾌적 상충) ·
  `portfolio_climate_candidates`(미래기후 시나리오별 공통·달라지는 후보) · `portfolio_criteria_candidates`(운영 부담·비용·쾌적 기준별 후보 집합) ·
  `scenario_versions/replay`(저장한 판을 다시 계산하지 않고 재생) — be-3d 추가 100 대응.
- 제거·값 변경 없음.

## 0.3.87 (2026-10-06, 태그 v0.3.87) — 연산 매니페스트: answer_reshape 다섯 연산 추가 · 파생 재생성

- 추가: `answer_reshape/distribution`(최소·중앙값·최대·우리 건물 위치) · `tie_groups`(동률 묶음) · `pin_set`(대상 목록 고정) · `location_check`(지도 위치 확인) · `conditions_issues`(대안별 성립 조건·남은 쟁점) — be-3d 추가 100 대응.
- 파생 재생성(게이트웨이 능력표에서 — 가산만): `climate_scenario_rank`·`measured_building_climate` 연도 축 · `measured_channel_coverage`·`scene_data_query` 월 축 · `perspective_reorder` 관점 인자 선택(질문 낱말로 채움).
- 제거·값 변경 없음(`cohort_query` 전기·가스 지표는 능력표 선언으로 유지).

## 0.3.86 (2026-10-06, 태그 v0.3.86) — measure_cost_catalog ECON 외기냉방(Economizer) 조치 가산 (스키마 v1.5)

- measure_cost_catalog(스키마 1.4→1.5): measures 에 ECON(외기냉방/엔탈피 이코노마이저, measure_ref ems:M02) 추가 → 12→13조치. savings_by_enduse cooling_elec 0.11 = KR2026B EnergyPlus 시뮬 M02 cooling_pct 유효쌍 grounding(B01 대형사무소 중앙값 10.9% 보수 채택, data_classification=simulation_derived — 조사 deemed 12조치와 방법론 구분, note 명시). CAPEX 600원/㎡ = ems_strategy_capex_assumption(M02) 파생.
- resource_authorization 허용 action_kind 14→15(catalog 13 + 2 operational).
- ⚠ measure_cost_catalog 는 load_schemas() 에 적재되어 measures 가산이 SOURCE_HASH 를 바꾼다(옛 'reference-only·SOURCE_HASH 무관' 주석 정정). 소비처 _generated_constants 는 SOURCE_HASH만 갱신(생성 상수·모델 값 불변).

## 0.3.85 (2026-10-06, 태그 v0.3.85) — 게이트웨이 새 연산 building_search · building_month_counts(가산)

- operation_manifest: building_search(주소·건물 이름으로 건물 찾기 · 같은 이름 후보 구분 · 개별 동/필지 합계 단위) · building_month_counts(건물마다 전기·가스 자료가 있는 달 · 두 채널 관측 범위가 다른 건물).
- 스키마·생성 상수·생성 모델 값 변경 없음.

## 0.3.84 (2026-10-06, 태그 v0.3.84) — 게이트웨이 새 연산 peer_monthly_benchmark · cohort_query 인자 role_tour·entry_candidates(가산)

- operation_manifest: peer_monthly_benchmark(우리 건물 월간 사용량 ↔ 유사 건물 월별 중앙값) · cohort_query role_tour·entry_candidates · building_id 가 배정 자산 번호도 받음.
- corpus: Lab editSceneNotes(장면 설명 교체) · flyCameraShot showRelation.
- 스키마·생성 상수·생성 모델 값 변경 없음.

## 0.3.83 (2026-10-05, 태그 v0.3.83) — 게이트웨이 새 연산 climate_scenario_rank · cohort_query data_gaps(가산)

- operation_manifest: climate_scenario_rank(미래기후 시나리오별 유형 순위·범위·유지 후보·현재 사용량 대 미래 증가율) · cohort_query 인자 data_gaps.
- corpus: Lab 발표·전시 진행 op(mountSceneChoice · pinSceneData · mountVirtualLayout · keepExampleScene) · 순회 overview.
- 스키마·생성 상수·생성 모델 값 변경 없음.

## 0.3.82 (2026-10-05, 태그 v0.3.82) — 게이트웨이 새 연산의 연산 매니페스트·질의 코퍼스(가산)

- operation_manifest: cohort_month_change(두 달 건물별 비교 — previous_month · same_month_last_year) 등 게이트웨이 새 연산 항목.
  게이트웨이는 적재 때 등록 연산과 매니페스트를 맞대 본다 — 이 판 없이는 새 연산이 있는 게이트웨이가 CI 에서 import 실패.
- corpus: Lab op 추가(controlPlayback · mountShowSummary · playExhibitionLoop · tourSelected waitTiles · 지표 지도 month · 시간 재생 latestMonths).
- 스키마·생성 상수·생성 모델 값 변경 없음.

## 0.3.81 (2026-10-05, 태그 v0.3.81) — 0.3.80 뒤 가산 묶음 릴리스(소비 저장소 CI 정합 회복)

근거 = 사용자 2026-10-05 '깃허브가 자꾸 실패한다 … 근본적으로 해결하라'. 0.3.80 태그 뒤에 들어간 스키마 변경으로 생성 상수만 재생성되고
핀·잠금·생성 모델이 따라가지 않아 소비자 CI(airos SSOT Drift Check · EC pytest · 8.simulation sentinel)가 빨갰다. 이 판으로 핀·잠금·상수를 한 번에 맞춘다.

- 가산(값 변경 없음): declared_assumptions 새 행(partial delivery·climate_year_interpolation·robust_strategy_comfort·palettes·
  assumption_flip_scenarios·weather_matched_day_pairs·zone_co2_plausibility) · 모델 카드 training_domain(학습 영역·외기 범위) ·
  venue/edge_registration/provision 25자리 건물번호·identity_scope · 시계열 표 행 상한 · operation_manifest 갱신.
- 생성 모델(_pydantic_models) 재생성(ai_model_registry·edge_registration·engineering_session·provision·venue).
- 도구: `bump_ec_pin.py` 가 작업 공간에서 EC 핀 소비자를 **찾아** 더한다(8.simulation/ems_transformer 가 목록 밖이라 v0.3.79 에 남았다).

## 0.3.80 (2026-10-02, 태그 v0.3.80) — 지역 해석 표: 구 중심 닻 좌표를 업무·상업 중심으로(데이터만 · 모양 불변)

근거 = 사용자 '지역의 가장 중심되는 곳' · '강남구는 번화가로' + 캠페인 `review_exchange/rounds/R083_gpt.md` 송파구 EUI 지도 점검(송파 '도심' 닻이
건물 수 최대 셀 = 마천동 저층 주거지).

- `data/region_resolver_table.json` 다시 생성(be-3d `scripts/gen_region_resolver_table.py` — 입력 닻 표 `anchors.json` 이 바뀌었다). 구 중심 닻
  259곳의 좌표 = 500m 격자 **비주거 연면적**(건물당 5만㎡ 상한) 최대 셀의 연면적 가중 중심(be-3d `scripts/gen_region_anchors.py
  commercial_core_point`). 닻 이름·id·개수(316)·해석 결과(지명 → 코드)는 그대로. 표의 `sources.anchors.sha256` 이 새 닻 파일을 가리킨다.
- 이 판에는 0.3.79 뒤에 들어간 `ems_strategies` M00 한글 이름 수정(125b530)도 함께 실린다.

## 0.3.79 (2026-10-01, 태그 v0.3.79) — 상품 고르기 응답 출처에 '한 번 해석' 가산(airo_product_route 1.1 · 가산)

근거 = 캠페인 `docs/CAPABILITY_FIRST_QUERY_DESIGN_2026-09-30.md` §3.1(2026-10-01 19:5x 사용자 결정 — 한 질문에 LLM 이 둘(상품 고르기 · 정형 변환) 돌던 것을
하나로: LLM 은 정형·칸·표현 방식만 뽑고 상품은 게이트웨이가 그 결과와 질의자 권한으로 정한다 · 규칙이 확실하면 LLM 없이).

- `Response.source` 열거에 `interpretation` 추가(화면 계약 airo-product-route/v1 의 칸·모양은 그대로). `model` 칸: llm 이면 필수 · rule·fallback 이면
  없음(1.0 그대로) · interpretation 이면 선택(해석을 LLM 이 했을 때만). `allOf` 를 두 조건(llm → 필수 · rule|fallback → 금지)으로 나눴다.
- 설명 갱신: 문서 설명 · `source`(1.1 의 rule = 선언 낱말이 실제로 걸려 한 상품만 가리킴 — 해석 LLM 이 돌았어도 상품은 낱말이 정해 model 없음) ·
  `Request.asker`(한 번 해석 경로에서 질의자가 쓸 수 없는 상품을 고르지 않는 데에도 쓴다 — 자료 접근 권한은 고른 상품의 입구가 본다).
- pydantic 모델 `airo_product_route.py` 다시 생성. 생성 상수 영향 없음.
- 시험: 새 `test_airo_product_route_0379`(열거 · 받음 5 · 막음 7 · 생성 모델) · `test_airo_product_route_0376` 의 판 단언을 1.0|1.1 로.

## 0.3.78 (2026-10-01, 태그 v0.3.78) — 연산 매니페스트를 채운다: 등록된 연산 420개의 요구 자료 선언(operation_manifest 0.2 · 가산)

근거 = 캠페인 `docs/ACCEPTANCE_INSPECTION_PLAN_2026-10-01.md` §3 G4('새 기능 = 기능 계약 한 곳 등록') · `docs/GENERALIZATION_PLAN_2026-09-28.md` §6.2 P0
('연산 요구자료 선언이 완결되지 않았다 — 정본 기본 operations={}' · §6.3 '등록 연산 0').

- `default.operations` 420개(키 = `도구` 또는 `도구/연산`) — 손으로 적지 않았다. 게이트웨이 생성기 `8.simulation/ems_transformer/tools/gen_operation_manifest.py`
  가 능력표(`capability_table.ROWS` — 대상 종류·질문 인자·내는 부분·축·입력 출처·구현·시뮬 팩)와 점포 연산 채널 표(`store_operations_brief`)에서
  파생해 쓴다. 정형 질문 스위치(QUESTION_FORMS) 꺼짐 418 · 켜짐 420 을 합쳤다(`registered_when`). `--check` 로 다시 지은 것과 같은지 본다.
- `needs` 어휘 = `default.needs_vocabulary`(배정 자산 자료 · 건물번호 공공 자료 · 지역 통계 · 원형 표 · 시뮬 팩 · 호출자 계열 · 외부 서비스 ·
  `subject_data_not_derived`) + `channel:<채널>`. 능력표로 정하지 못한 25행은 '자료 없음'이 아니라 **못 잼**(`subject_data_not_derived`)으로 적는다.
- `default_period` 낱말 추가: `tool_rule`(도구 구현의 기본 기간 규칙 — 매니페스트가 아직 정하지 않음) · `not_applicable`(시간 축 없음). 점포 채널
  연산 23개만 `coverage_of_needs`.
- `Operation` 칸 추가: tool · operation · selector · subject_kinds · required_arguments · produces · axes · input_source · implementation ·
  comparison_unit · registered_when. 뿌리 칸 추가: generator · derivation_ko · operation_count · needs_vocabulary. 0.1 칸·필수·기간 낱말은 그대로
  (시험이 v0.3.77 태그와 맞댄다). `_usage` reference-only → runtime-validate(게이트웨이 능력표 적재 검사가 읽는다 — 등록된 연산마다 항목,
  검사 0건 = 실패). pydantic 모델 `operation_manifest.py` 다시 생성.
- 시험: 새 `test_operation_manifest_0378`(기본 표가 스키마를 통과 · 420 항목 키·어휘 · 막아야 할 항목 6 · 받아야 할 항목 3 · 못 잼 이름 · 0.1 칸 보존).

## 0.3.77 (2026-10-01, 태그 v0.3.77) — 값의 종류 배지 낱말 · 방법 한 줄 · 합성 시연 자료 별칭(data_classification 1.5 · 가산)

근거 = 캠페인 `docs/UIUX_CONSISTENCY_RESEARCH_2026-10-01.md` 결정 U1(배지 '측정 → 실측' · '참고치 → 참고' — 사용자 10-01 15:5x) · U4(분류가 없는 값 =
'표시 없음') · §2 '배지 낱말·짧은 방법 줄 = EC data_classification(badge_ko·short_ko)' · 표 H1(AgentLeague 합성 시연 자료 `synthetic_demo_fixture` 가
어휘 밖 낱말이라 '못 잼 · 분류 미표시'로 보였다).

- `default.classification.display_badges_ko` = 표시 등급(EvidenceDisplayClass 8개 — 순서 그대로) → 화면 배지 낱말 7개(실측 · 예측 · 추정 · 참고 · 가상 ·
  혼합 · 가상 · 표시 없음 — synthetic 과 virtual 은 둘 다 '가상').
- `words[*].badge_ko`(= `display_badges_ko[display_class]` — 시험이 낱말마다 본다) · `words[*].short_ko`(방법 한 줄 — 명사형 · 표마다 한 번 보이는 짧은 글:
  계량기 기록 · 시뮬레이션 · 실측에 맞춘 모델 · 빈 값 채움 · 공공 기준표 · 질문에 적힌 값 · 기본 가정 · 연습용 가상 값 …).
- 별칭 `synthetic_demo_fixture → virtual`(배지 '가상').
- 기존 낱말 · `label_ko` · 별칭 · 합성 규칙은 하나도 바꾸지 않았다(시험이 v0.3.76 태그와 잎마다 맞댄다). 생성 상수(`DATA_CLASSIFICATION_VOCAB` — 표 통째)는
  새 칸을 그대로 싣는다(`gen_constants --all` · `--check` drift 0).
- 시험: 새 `test_classification_badges_0377`(표시 등급 8 · 낱말 17 · 반례 — 추정에 '실측' · 모름에 '가상' 금지 · 별칭 받아야 할 3 · 막아야 할 5 ·
  v0.3.76 태그 대조 · 생성본).

## 0.3.76 (2026-10-01, 태그 v0.3.76) — 통합 화면 상품 고르기 계약 airo_product_route 1.0(새 스키마 · 가산)

근거 = 캠페인 `docs/INTEGRATED_INTERFACE_AND_LLM_ROLE_RESEARCH_2026-10-01.md` D1(사용자 결정 10-01 09:5x — 심사위원 시연은 통합 화면 Studio `/stage` ·
질문 상자 하나 · LLM 이 상품을 고르고 칩으로 보이며 사용자가 바꾼다 · 질의자는 고른 상품이 정한다) · 화면 세션과 합의한 계약 `POST /v2/route-product`.

- 새 `airo_product_route.json`(airo-product-route/v1, `_usage` runtime-validate · 소비처 ems_transformer · energy-decision-studio):
  `$defs/Request{question_ko, surface: const stage, asker?, prior_product?, continuation?{prior_request_id, prior_question_ko?}}` ·
  `$defs/Response{schema: const airo-product-route/v1, product, why_ko, alternatives[≤2]{product, why_ko}, source: llm|rule|fallback, model?}` ·
  `$defs/Product` = studio · airos · be3d · agentleague · mcp · `$defs/WhyKo` = 2~120자 · 줄바꿈 없음. 모두 `additionalProperties: false`.
  `model` 은 source=llm 일 때만(있어야 한다), rule·fallback 이면 없다. 문서 뿌리 = oneOf(요청 | 응답).
- 질의자 모양은 사본을 두지 않고 `airo_request.json#/$defs/Asker` 를 가리킨다(파일 밖 $ref — 검사는 두 문서를 한 레지스트리에). 질의 봉투
  `airo_request` 는 그대로(표면 목록에 stage 를 넣지 않는다 — 상품 고르기는 자기 계약). 대안 상품이 서로 다르고 고른 상품과 다르다는 규칙은
  JSON Schema 로 적을 수 없어 게이트웨이 코드(`serving/product_router.py`)가 검사한다. 상품 역할 글·예문·규칙 낱말은 게이트웨이 상품 표 한 곳 — 이
  스키마는 이름만 정한다.
- `_index.yaml` 등재 · pydantic 모델 `airo_product_route.py` 생성. 생성 상수 그대로(runtime-validate: `gen_constants --all` 12 소비처 SAME · `--check` drift 0).
- 시험: 새 `test_airo_product_route_0376`(받아야 할 요청 6 · 막아야 할 요청 18 · 받아야 할 응답 6 · 막아야 할 응답 18 · 질의자 정본 정의 대조 ·
  질의 봉투 표면 목록 불변 · 색인 · 생성 모델).

## 0.3.75 (2026-10-01, 태그 v0.3.75) — 요청 봉투 표면 이름 canvas(airo_request 2.6 · 가산)

요청 = 화면 세션(캠페인 `scratch/capability_first/requests_round3.md` 주 세션 메모 06:25 — energy-decision-canvas :3030 이 6단계 흐름도를 v2 질의 한 번으로
채운다). 캔버스는 이미 `surface: "canvas"` 를 보내고, 2.5 봉투는 목록 밖 이름이라 422 로 거절했다.

- `airo_request` 2.5 → 2.6: `properties.surface.enum` 뒤에 `canvas` 하나를 붙이고 `surface` 에 설명을 단다. 앞 다섯 이름·순서는 그대로 —
  2.5 에서 유효한 봉투는 2.6 에서도 유효하고, 목록 밖 이름(`Canvas` · `canvas ` · 앱 폴더 이름 · 빈 글 …)은 여전히 거절한다.
  canvas 가 따르는 규칙(Studio 와 같은 선언 공무원 표면 — 질의자·화면·도구·신원)은 스키마가 아니라 게이트웨이 한 곳이 정한다.
- 생성 상수 그대로(runtime-validate 스키마: `gen_constants --all` 12 소비처 SAME · `--check` drift 0) · pydantic 모델 `airo_request.py` 재생성
  (`Surface.canvas` · surface 설명).
- 시험: 새 `test_airo_request_surface_canvas_0375`(받아야 할 canvas 봉투 5 · 2.5 봉투 7 · 막아야 할 봉투 14 · v0.3.74 태그와 잎 전부 대조 ·
  생성 모델의 표면 목록 = 스키마 목록) · `test_interface_contracts_0362` 의 봉투 판 고정 2.5 → 2.6(근거 주석).
- 소비처 뒤처리: 게이트웨이 봉투 판 고정 시험(`tests/test_m3g_envelope_v23.py`)은 2.6 으로 — 게이트웨이 묶음 끝에 함께.

## 0.3.74 (2026-10-01, 태그 v0.3.74) — 게이트웨이 3회전 묶음이 기다리는 행(요청 E4-1 · E5-1~3 · E6-1~3 · R3F-1~3 · WP2 §4 · 가산)

요청 = 캠페인 `scratch/capability_first/EC_ROWS_NEEDED_round3.md` · `requests_round1.md` WP2 §4(설계 `docs/CAPABILITY_FIRST_QUERY_DESIGN_2026-09-30.md`).
0.3.73 의 키와 값(문구 포함)은 하나도 바꾸지 않았다 — 예외는 판 표지와 원형 별칭 목록 셋의 **뒤에 붙이기**뿐(시험이 태그와 잎마다 맞댄다).

- `building_usage_map` 1.2 → 1.3: 용도 별칭 `사무실 → 업무시설`(사무소·오피스와 같은 일상어 — 면적 모름 = 중형 + '면적 미확인') ·
  `usages.convenience_store.operates_24h = true`(선언 가정 — 게이트웨이 가상 일정 `_virtual.OCCUPIED_HOURS['RET']` 값 그대로 · ⚠
  `calendar_conventions.day_windows.outside_hours_store` 의 이름표 '영업 외(1~7시)'와 뜻이 어긋난다 — 결정은 EC 소유자·사용자) ·
  `usage_archetype.rows[*].archetype_relation`(same_type | nearest_other_type + `relation_basis_ko` — 편의점·교육연구시설·근린생활·공장·확장 용도 =
  가장 가까운 다른 종류) + 관계 어휘 `usage_archetype.archetype_relations`. 요청은 `usages[*]` 에 두자고 했으나 원형을 정하는 표(rows)에 두었다 —
  1.2 가 usages 에 원형 사실을 손으로 적지 않기로 한 규칙 그대로.
- `building_archetypes` 2.2 → 2.3: 원형 별칭 B01 '큰 사무실·대형 사무실·큰 오피스' · B02 '중형 사무실' · B03 '작은 사무실·소형 사무실·작은 오피스'
  (DOE 규모 구간의 어휘 결정 — '큰'은 면적을 말하지 않는다) · `doe_buildings[*].electricity_price_class`(주택 원형 B16·B17·B18 = 주택용 · 학교 B07·B08 =
  교육용 · 나머지 = 일반용 — 규칙 `electricity_price_class_rule`) · `sim_axes.scenario_names`(현재 기후 · 2050년 SSP2-4.5 · 2050·2080년 SSP5-8.5 — 근거 = 기상 파일 계보 ·
  IPCC AR6 이름).
- `target_vocabulary` 1.1 → 1.2: `gas_price_classes`(주택용 · 산업용 — 값은 `market_prices.retail_reference_2026.gas_retail_seoul` 을 가리키기만) ·
  `air_asset_kinds[*].gas_price_class`(HOM = residential · FAC = industrial · BLD·RET·PRT = null → 참조 단가 `unit_prices.gas_krw` 그대로 — 기존 요금이 움직이지 않는다) ·
  `$defs.AirAssetKindEntry` 에 이미 쓰던 `electricity_price_class` 와 새 `gas_price_class` 선언.
- `ems_strategies` 3.4 → 3.5: `strategies[*].easy_name_kr`(쉬운 이름 23 — 조합은 `easy_name_rule` 로 구성 대책 이름을 이은 글 · 적재 검사가 같은지 본다) ·
  단일 전략 `setpoint_action`(어휘 `setpoint_actions`: M04·M05 comfort_band_dynamic · M16 night_setback · M09 pre_peak_shift · M00 fixed_with_night_setback ·
  **M10 peak_hour_setup** — 요청은 '나머지 none' 이었으나 8.simulation `docs/PHYSICS_SPEC_2026-09-15_CONTRACT.md` §5 M10 VB 가 14~17시 냉방 설정 +2℃ 를 적어 그대로 옮겼다 ·
  나머지 none) · `applies_when`(M00·M06·M16 비운영 시간 · M01 날마다 켜고 끔 · M03 여러 대 · M08 기계 환기 · M18 ESS — 어휘 `applicability_conditions`,
  전제를 가르는 대상 사실 = 용도 칸 `operates_24h`).
- `declared_assumptions` 1.5 → 1.6: 새 행 셋 — `operation_reading_window`(28일 · 7일 · 구성원 12곳 — decision_support 리터럴 그대로) ·
  `operation_reading_freshness`(읽은 창이 오늘과 같은 철이면 '지금 운전' — 설계 §2.5 한계 4 '한 철' · 계절 = `calendar_conventions.question_season_system` ·
  새 수는 0 하나) · `cohort_city_min_share`(0.5 초과 — 낱말 '다수결'의 뜻). 기존 행 값 안에 `serving_display_limits.value.display_significant_digits`(3 —
  measure_candidates 리터럴 그대로). 요청이 제안한 `operations_proxy_rules.value` 대신 새 행으로 둔 까닭: 그 value 는 게이트웨이 경제성 수명 격자 가정
  (`_assumption_ranges.declared_parameter`)이 통째로 답에 싣는다 — 칸을 더하면 옛 답 바이트가 바뀐다.
- 적재 검사 `scripts/vocabulary_gate.py`: 새 칸이 가리키는 열쇠(원형 전기 종별 · 자산 가스 종별과 그 `market_prices_ref` 가 수를 가리키는가 · 설정 동작 · 적용 전제와
  그 대상 사실 · 조합 쉬운 이름 = 구성 이름을 이은 글 · 쉬운 이름 겹침 · 용도→원형 관계 · 운전 기록 나이의 계절 체계) — 칸이 있을 때만 돈다(0.3.73 모양은 통과).
- 넣지 않은 것(근거 없음 · 결정 몫): M01 끄는(정지) 시각 서명(R3F-4 — 새 문턱이고 인용할 근거가 없다) · 효과 결함 설비 정본 자리와 H_D(R3F-5 — 시뮬 세션·사용자) ·
  설비 라벨 이름(E4-2 — 시뮬 세션이 템플릿 계보에서).
- pydantic 모델 재생성: building_usage_map · building_archetypes · target_vocabulary · ems_strategies. 생성 상수: `gen_constants.py --all` 12 소비처 재생성 · `--check` drift 0.
- 시험 `tests/test_ec_rows_0374.py`(새 — 요청 값 · 0.3.73 태그와 잎 전부 · 검사가 막을 것 17 · 통과시킬 것 5 · 생성본 도달 · 넣지 않은 요청) · 0.3.70 시험의 새 행 개수(+3)와
  `test_interface_contracts_0362` 의 declared_assumptions 판 고정(1.6)을 근거와 함께 갱신.

## 0.3.73 (2026-10-01, 태그 v0.3.73) — 요청 봉투 2.5: 고른 해석 `interpretation`(선택 칸 · 가산)

근거 = 캠페인 `docs/CAPABILITY_FIRST_QUERY_DESIGN_2026-09-30.md` 결정 14 · 화면 세션 합의 `scratch/capability_first/screen_contract_agreed_with_f7.md`.
화면(Studio·AIROS)은 답의 '고를 질문'(`validation.suggested_questions[]`)을 누르면 이 칸을 보내는데, 2.4 봉투는 모르는 칸을 거절했다.

- `airo_request.json` 2.4 → 2.5: 봉투 최상위 `interpretation` = `$defs.Interpretation{frame_id, from_request_id?}`.
  `frame_id` = 1~64자 `[A-Za-z0-9_.:-]`(필수) · `from_request_id` = 1~120자(봉투 `request_id` 한도와 같다). 모르는 칸 금지.
  뜻: 게이트웨이가 질문 글을 다시 해석하지 않고 고른 정형 질문으로 실행한다. 대상·기간은 이 칸이 정하지 않는다.
  2.4 에서 유효한 봉투는 그대로 유효하다(칸이 없으면 게이트웨이 요청 바이트가 달라지지 않는다).
- 어떤 `frame_id` 가 켜져 있는지는 스키마가 아니라 게이트웨이 정형 질문 표가 정한다(이 스키마는 모양만).
- 생성 상수: 변화 없음(`airo_request` 는 runtime-validate — `gen_constants.py --all` 12 소비처 SAME · `--check` drift 0). pydantic 모델 `airo_request.py` 재생성.
- 시험 `tests/test_airo_request_interpretation_0373.py`(새 — 받아야 할 것 8 · 막아야 할 것 13) · `test_interface_contracts_0362` 의 봉투 판 고정을 2.5 로(근거 주석).
- 소비처가 맞출 것: 게이트웨이 시험 `tests/test_m3g_envelope_v23.py` 의 봉투 판 고정(2.4) — 게이트웨이 묶음 끝에서 2.5 로.

## 0.3.72 (2026-09-30, 태그 v0.3.72) — 일반화 단계 소비처가 기다리는 행(요청 C1~C11 · WP6 R10 · 가산)

요청 = 캠페인 `scratch/wp_requests/EC_ROWS_NEEDED.md`. 0.3.71 의 키와 값은 하나도 바꾸지 않았다(문구 포함) — 예외 하나 = 사용자·EC 소유자 결정인
`calendar_conventions.question_season_system`(null → `meteorological`)과 그 설명 문장. moved_literal = 오늘 코드 리터럴 값 그대로.

- `declared_assumptions` 1.4 → 1.5: 새 행 33 — `demo_user_answers`(C11) · `economics_horizon_years_default` · `financial_candidate_measures_max` ·
  `climate_load_shift`(C9) · `facility_use_classes`(무더위 쉼터 후보 — estimated, 원문 대조 전) · `small_building_area_m2_default` · `cohort_bands_default` ·
  `cohort_segmentation_default`(C10) · `forecast_horizon_default` · `period_substitution` · `ranking_basis_default` · `schedule_event_nouns`(C5) ·
  `drop_sustain_share_of_threshold`(C8) · `quadrant_split_default` · `priority_axis_defaults`(C4) · `debate_axis_scales`(법규 = 1 — 셈 단위 축) ·
  `debate_recalc_fixtures` · `debate_numeric_rules` · `debate_calendar` · `debate_family_critics`(C6 — 기존 debate_* 행은 그대로) · `indoor_design_rh_pct`(C3) ·
  `diagnosis_risk_thresholds` · `home_baseload_low_share` · `appliance_exhaustive_search_max` · `drop_reference_days_default` · `drop_integrity_rule`(C7) ·
  `action_review` · `virtual_action_effects` · `lhs_axis` · `virtual_start_shift` · `sim_pack_analysis_defaults` · `virtual_population_shares`(C2) ·
  `policy_adverse_boundary`(WP6 R10 — 부호 정의 0).
  기존 행 값 안에 새 칸: `hazard_week_scenarios.value.cold`(0 · −2 · −4℃) · `serving_display_limits.value.presentation_table_max_columns`(12)·`presentation_chart_max_series`(6) ·
  `scene_motion_defaults.value.descend_keys`·`dive_building_end_alt_m`(250) · `sim_schedule_inference.value.morning_window_hours`(12)·`startup_window_hours`(2)
  — 뜻은 행 수준 `value_notes_ko`(rule_ko 문장은 그대로 — 답 바이트 보존). `comm_status_thresholds.by_delivery.<프로필>.label_ko`.
- `calendar_conventions` 1.1 → 1.2: `question_season_system = "meteorological"`(계절 넷을 모두 가진 유일한 체계 — 봄 3~5 · 여름 6~8 · 가을 9~11 · 겨울 12~2) ·
  `question_season_system_basis`.
- `equipment_taxonomy` 1.2.0 → 1.3.0: `aliases_ko`(C8 표 + C2 추가) · `labels_ko`(capability_matrix 20종 → name_ko + aliases_ko — aliases_ko 를 모두 담고 질문 말 냉방·냉동고·온돌) ·
  `dr_class`(DR_CLASS_TABLE 을 종류로 — plug 는 유지, 끌 수 있는 가상 충전은 dr_three_stage) · `$defs.DrClass`. 모델 재생성.
- `measure_cost_catalog` 1.3 → 1.4: 조치 12개 전부 `aliases_ko`. 모델 재생성.
- `ems_strategies` 3.3 → 3.4: M00 · M01 · M10 · M16 `observable_signature`(decision_support._mcode_candidates 문턱 값 그대로). 모델 재생성.
- `data_classification` 1.3 → 1.4: `words.estimated.aliases_ko` [근사, 범위]. `target_vocabulary` 1.0 → 1.1: `air_asset_kinds.{HOM,RET,BLD}.aliases_ko`. 모델 재생성.
- `region_codes` 2.4 → 2.5: 시뮬 도시 18곳 `coastal` + `coastal_basis`(행정구역이 바다에 닿는가 — 지리 선언). ⚠ 옛 코드 `_COASTAL_CITIES`(부산·인천)보다 넓다:
  울산·강릉·제주·포항·창원·목포도 해안. 모델 재생성.
- `error_response` 1.2 → 1.3: Refusal.retry 열거 += `later`(일시 장애). 모델 재생성(error_response · airo_result · interface_types).
- `judgement_thresholds` 1.2 → 1.3: `anomaly.robust_z`(수정 z 3.5 · 이상 · MAD × 1.4826 — Iglewicz & Hoaglin 1993).
- 넣지 않은 것: `review_task_roles`(검토 역할 이름 = 재구성 등록부 어휘) · 판정 정책 값 둘(env·설정) · `storage_capex_krw_per_kwh`·
  `home_appliance_replacement…new_saving_share_range`·`ai_model_registry…training_domain`(요청이 값·근거를 정하지 않았다 — 지어내지 않는다).
- 적재 검사 `scripts/vocabulary_gate.py`(새): 스키마를 훑어 어휘 표를 **찾아서**(손 목록 없음) 한 별칭 = 한 열쇠 · 가리키는 열쇠 존재(설비 종류 = capability_matrix ·
  분류 = ClassificationWord · 용도 = EndUse …) · 질문 계절 체계가 계절 넷을 덮는가. `gen_constants.load_schemas`(결함이면 생성 안 함) ·
  `validate_ssot --check schemas` 가 같은 함수를 부른다.
- 시험 `tests/test_declared_assumptions_0372.py`(새) · 0.3.70/0.3.71 시험의 고정 개수·판 번호를 0.3.72 근거와 함께 갱신.

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
