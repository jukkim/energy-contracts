# 건물 식별 어휘 대응표 (SSOT)

> 25자리 건물관리번호(`bld_mgt_sn` / `building_mgmt_no`)가 **물리 건물의 주요 식별자**다.
> 19자리 PNU(`pnu` / `parcel_id`)는 **필지** 키이며 건물을 특정하지 않는다(한 필지 여러 동).
> 두 이름이 스키마마다 다른 것은 역사적 이유다: `building_model_packet.BuildingIdentity` 는 `bld_mgt_sn`(대장 컬럼명),
> `building_passport.identity` 와 airos 는 `building_mgmt_no`. **값은 같다.**

## 생산자(be-3d / airos) 상태 ↔ `BuildingIdentity` (model_packet) ↔ 여권 v1.2

| 생산자 `building_mgmt_no_status` | `identifier_kind` | `identity_status` | `selected_identifier_match_status` | 여권 `physical_identity` | 여권 `identity_match_status` |
|---|---|---|---|---|---|
| `verified` (소유자 원장 결정) | official_building | canonical | exact | building | exact |
| `candidate_physical` (필지 위 번호 동 하나·번호 없는 행 0, 또는 Juso 정확 일치) | official_building | provisional | probable | building | probable |
| `candidate` (사람 선택 / 번호 없는 footprint 공존 / 여러 필지에 걸린 번호 / 주소 다중 매치) | official_building | provisional | probable | building | probable |
| `ambiguous` (여러 동, 후보 목록 동봉) | parcel_proxy | provisional | unmatched | parcel | unmatched |
| `not_found` (필지는 있으나 번호 없음) | parcel_proxy | provisional | unmatched | parcel | unmatched |
| `unverified` | parcel_proxy(필지 있음) / virtual_asset | provisional | unmatched | parcel / none | unmatched |
| airos `anonymized` (원본 비식별 데모 건물) | virtual_asset | provisional | unmatched | none | unmatched |
| airos `virtual` (99* 가상 필지) | virtual_asset | provisional | unmatched | none | unmatched |
| airos `service_error` (못 잼 — 판정 아님) | (packet 미발행) | — | — | none | unmatched |
| airos `not_applicable` (설계상 공간 식별 없음, 근거 문서 명시) | virtual_asset | canonical | unmatched | none | unmatched |

geocode `match_basis` → 필지 등급: `juso_bdMgtSn_exact` → candidate_physical · `juso_pnu_prefix` / `juso_bdMgtSn_conflict` / `vworld_nearest_footprint` → candidate.

## 원칙 (모든 저장소 공통)

1. 25자리는 **만들지 않는다**. Juso `bdMgtSn` 또는 `building_footprints.bld_mgt_sn` 에서만 온다. 19자리에서 파생 금지.
2. `verified` 는 해석기가 내지 않는다. 사람의 결정이 원장(누가·언제·목적·범위·id)과 함께 적용된다. 상류의 "verified"(대장 정확 일치)는 소비자에서 `candidate_physical` 로 받는다.
3. 다동 필지는 `ambiguous` + 후보 목록. 조용히 한 동을 고르지 않는다. 고르면 근거(주소 좌표 거리·대안 동)를 남기고 `candidate`.
4. 필지 키 에너지(`energy_results`)는 필지 footprint 가 하나일 때만 건물 값이다. 응답에 `energy_scope` / `building_use_allowed` / `metric_scope` 를 싣는다.
5. 상태값은 위 표 밖의 단어를 쓰지 않는다. 소비자는 모르는 단어를 `unverified` 로 받는다.

## 파일 소재

- 여권: `energy_contracts/schemas/building_passport.json` (v1.2 `identity.identity_match_status`)
- 모델 패킷: `energy_contracts/schemas/building_model_packet.json` `$defs.BuildingIdentity`
- 에이전트 입력: `energy_contracts/schemas/agent_contracts.json` `BuildingContext` — **아직 `pnu`(필지) 만**. `building_mgmt_no` 추가는 다음 태그 릴리스로 보류(DEFERRED_INTEGRATIONS 참조). 그때까지 A01 등 에이전트 입력은 필지 단위다.
- 생산자: `building-energy-3d/src/visualization/{search,smart_building,buildings_detail}.py`
- 소비자: `airos-energy-decision/src/airos_energy_decision/{adapters/be3d,spatial_identity,asset_registry,routing}.py`
- 게이트: `airos-energy-decision/tools/verify_spatial_identity.py`
