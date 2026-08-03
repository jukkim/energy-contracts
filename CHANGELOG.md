# Energy Contracts — CHANGELOG

스키마·프로토콜 변경 이력. 필드 추가는 minor, 삭제·이름 변경은 major.

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

## v0.3.31 — 2026-08-01

### provision v1.4 — 건물별 **점 설정** (`OperatingConfig.point_settings[]`)

건물마다 내릴 수 있는 축이 `objective` **하나뿐**이었다. 실제 관제는 설정온도·조명·
스케줄처럼 **점(point) 단위 값**을 건물마다 다르게 준다. 엣지엔 점 제어 계층이 이미
있는데(`onsite/`: DeviceCatalog·Scope·Executor·value_spec) **원격에서 들어갈 계약이
없었다** — 그래서 mgcc 가 `setpoints.default_c` 같은 키를 지어 보냈고,
`additionalProperties` 가 열려 있어 검증을 통과한 뒤 **아무도 읽지 않았다**.
성공 ack 까지 돌아오는데 설비는 안 움직이는 상태였다(mgcc §5.9).

**세 축이 직교한다** — 이게 이 계약의 골자다:

| 축 | 필드 | 값 |
|---|---|---|
| ① 무엇을 지목하나 | `point_id`(CPA 정확 지목) / `selector`(다중) | 둘 중 **하나** |
| ② 어떤 성질의 점인가 | `kind` | physical · virtual · group · schedule |
| ③ 값이 어떻게 생겼나 | `value` / `values[]` / `schedule[]` | 셋 중 **정확히 하나** |

- `role`(sensor·sp·**cmd**) — 쓰면 설비가 움직이는 점을 값에 섞지 않고 따로 밝힌다.
  권한·감사가 달라야 하는 축이다.
- `priority` 기본 **16**(BACnet 관례의 최하위) — 원격 설정이 현장 수동 조작이나
  생명안전 인터록을 밀어내지 않는다.
- `schedule` 은 **현장 시각**이다(UTC 아님 — 사람의 시간표다). `start > end` 는
  자정을 넘는 구간(야간 셋백). 겹치면 **뒤 항목이 이긴다**(순서가 뜻을 가지므로
  소비단이 재정렬하면 안 된다). 어디에도 안 걸리면 `fallback`, 없으면 **직전 값
  유지** — 임의 기본값으로 떨어뜨리면 밤중에 설비가 제멋대로 움직인다.
- **빈 배열 = 전부 해제**. 미제공(무변경)과 구분된다.
- **부분 성공**: 항목 하나가 안 먹어도 나머지는 적용된다. 소비단은 항목별 결과를
  ack 에 담는다.
- `selector` 매칭 0건은 오류가 아니라 `matched: 0` 이다 — 없는 설비를 있다고 하지
  않는다. 현장 device_id 는 발행자가 알 수 없으므로 **엣지가 자기 카탈로그로 푼다**.

⚠ **guarded mirror**: `kind`·`role`·`selector.equipment_kind` 는 각각 telemetry
`PointKind`·equipment_taxonomy `PointRole`·`EquipmentKind` 의 복제다. 교차 파일
`$ref` 는 일반 검증기가 못 푼다(실측 `Unresolvable`). `tests/
test_point_setting_contract.py` 가 원본과 같은지 매 실행 확인한다 —
**읽을 때와 쓸 때 같은 점을 다른 이름으로 부르면** 소비단마다 뜻이 갈린다.

codegen drift 0 (provision 은 상수 생성 대상이 아니다).

---

## v0.3.30 — 2026-08-01

### provision v1.3 — `config.operating` 선언 (에이전트 동작 특성)

생산자(mgcc `provisioner.operating_config`)와 소비자(edge-agent
`persona_registry.resolve_persona_from_operating`)가 **둘 다 있는데 계약만 침묵**했다.
`additionalProperties` 가 열려 있어 통과는 했지만 **검증도 발견도 안 됐다** —
스키마를 보고 이 필드의 존재를 알 방법이 없었다.

- `$defs.OperatingConfig` — `objective` + `customProfiles[]`
- **발령과 다른 축**: 평시 운영의 주체는 **엣지 에이전트(APE)** 다. 이 블록은
  에이전트에게 *어떤 성향으로* 돌리라고 말하는 것이지 *지금 무엇을 하라* 는 명령이
  아니다. 명령은 `dr_dispatch_event` 이고 발령 창 동안만 유효하다 — 이쪽은 해제할
  때까지 지속된다.
- 미제공 시 엣지는 **자기 설정을 유지**한다(빈 블록으로 초기화되지 않는다)

⚠ `objective` 값집합은 `ems_strategies.json#/$defs/ObjectiveType` 의 **guarded
mirror** 다. 교차 파일 `$ref` 는 일반 jsonschema 검증기가 풀지 못해(실측) 복제했고,
`tests/test_canonical_value_gate.py` 가 매 실행 원본과 대조한다.

효과: 미지원 objective 가 **이제 거부된다**(선언 전에는 그냥 통과했다).
생성 상수 drift 0.

## v0.3.29 — 2026-08-01

### equipment_taxonomy v1.1.0 — 설비별 표준 관제점 집합(point_sets)

EquipmentKind 는 "무엇인가"만 말하고, 그 설비에 **어떤 점이 있어야 하는가**는 아무
데도 없었다. 그래서 소비단마다 점 목록을 손으로 적었다.

- $defs.PointRole (sensor/sp/cmd) — Project Haystack 의 3분 그대로. 이 3분이
  "읽기만 하는 점"과 "쓰면 설비가 움직이는 점"을 가른다.
- $defs.EquipmentPoint + default.point_sets — 설비 12종 · 점 44개
- 각 점에 Brick 클래스 / Haystack 태그 조합을 연결(외부 온톨로지 접점)

**근거**: Project Haystack 4 lib-phIoT 설비 proto · Brick Schema point classes ·
ASHRAE Guideline 36-2024 AHU Controls Points Lists(규범 참조 — 본문 비공개라
목록을 복제하지 않았다). 출처는 default.point_sets_sources 에 남긴다.

⚠ **기대치이지 강제가 아니다**. 현장마다 계측 범위가 다르므로 빠진 점은 "위반"이
아니라 "미계측"이다 — 없는 것을 있다고 하지 않기 위한 근거다.

⚠ 니모닉은 **CPA {point} 세그먼트와 같은 어휘**(bems-console MNEMONICS 정본)를 쓴다.
표준은 "어떤 점이 있어야 하나"의 근거로만 쓰고 이름은 기존 어휘를 유지한다 —
표준 이름을 그대로 들여오면 주소 어휘가 갈린다.

생성 상수: SOURCE_HASH 만 변경(point_sets 는 export 화이트리스트 밖) — 소비 6 repo
해시 동기 필요, **값 변화 없음**.

## v0.3.28 — 2026-08-01

### telemetry v1.4 — 관제점 종류·바인딩 + CPA 건물 세그먼트

- **$defs.PointKind** 신설 (physical/virtual/group/schedule). 소비단이 "이 값이 실제
  계측인가"를 알아야 한다 — 가상점을 실측처럼 표시하면 화면이 거짓이 된다.
- **$defs.PointBindingMode** 신설 (bacnet/modbus/opcua/mqtt/internal/derived).
  주소(CPA)와 바인딩은 **다른 축**이다 — CPA 는 "무엇인가"(식별), 바인딩은
  "어디에 연결됐나"(경로). 같은 점이 프로토콜을 바꿔도 CPA 는 유지된다.
- `zones[].point_kind` / `zones[].binding_mode` 추가 (둘 다 optional).
  **배경**: MGCC `points.py` 가 이미 이 두 필드를 읽고 있었는데 계약에 정의가 없어
  **항상 null** 이었다 — 받는 쪽은 있는데 보낼 방법이 없던 상태.
- **CanonicalPointAddress 에 선택적 `{building}` 세그먼트**:
  `{country}.{site}[.{building}].{domain}.{equip}.{point}`.
  한 site 에 건물이 여럿이면 site 만으로 "A동 3층 AHU"와 "B동 3층 AHU"를 구분할 수
  없다. 캠퍼스·산단·단지처럼 MG 가 다루는 단위가 바로 그런 곳이다(MGCC 수용가 30동).
  **5-세그먼트 기존 주소는 그대로 유효**(하위호환).
  파싱은 세그먼트 **수**가 아니라 **domain 값**으로 위치를 찾는다 — 개수로 갈라 읽으면
  새 domain·계층이 생길 때 조용히 깨진다.

생성 상수 drift **0** — telemetry 는 페이로드 스키마라 codegen 대상이 아니다.
(이 변경을 "6-repo 재생성 캐스케이드" 때문에 미뤄 뒀었는데, 실제로 재보니 캐스케이드가
없었다. 측정하지 않고 비용을 추정한 것이 미룬 이유였다.)

소비단 갱신: bems-console `lib/point-address.ts`(정본 파서, 5~6계층 지원) ·
mgcc `points.py`(자체 어휘 `field`/`virtual` → EC 두 축으로 교체).

## telemetry v1.4 — 관제점 종류·바인딩 + CPA 건물 세그먼트

- **$defs.PointKind** 신설 (physical/virtual/group/schedule). 소비단이 "이 값이 실제
  계측인가"를 알아야 한다 — 가상점을 실측처럼 표시하면 화면이 거짓이 된다.
- **$defs.PointBindingMode** 신설 (bacnet/modbus/opcua/mqtt/internal/derived).
  주소(CPA)와 바인딩은 다른 축이다 — CPA 는 "무엇인가", 바인딩은 "어디에 연결됐나".
-  /  추가 (둘 다 optional).
  **배경**: MGCC  가 이미 이 두 필드를 읽고 있었는데 계약에 없어 **항상
  null** 이었다. 받는 쪽이 있는데 보낼 방법이 없던 상태.
- **CanonicalPointAddress 에 선택적 {building} 세그먼트**
   — 한 site 에 건물이 여럿이면
  site 만으로 "A동 3층 AHU"와 "B동 3층 AHU"를 구분할 수 없다. 캠퍼스·산단·단지처럼
  MG 가 다루는 단위가 바로 그런 곳이다(MGCC 수용가 30동).
  **5-세그먼트 기존 주소는 그대로 유효**(하위호환).
  파싱은 세그먼트 수가 아니라 **domain 값**으로 위치를 찾는다.

생성 상수 drift **0** — telemetry 는 페이로드 스키마라 codegen 대상이 아니다.
소비단 갱신: bems-console (정본 파서) · mgcc .

## 0.3.27 — 2026-07-31 provision config_merge — 단일 축 하달이 설정을 지우던 것 (additive = minor)

v0.3.26 로 MGCC 가 설정을 하달할 수 있게 됐지만, **보내면 안 되는 상태**였다. 수신측은 `config` 를 로컬 YAML 로 **통째로 저장**한다(`_save_yaml` 이 전체 문서를 덮어씀). MGCC 는 운영 모드·계약전력만 관장하므로 그 축만 담아 보내는데, 그러면 엣지의 `kind`·`backend`·`connection` 이 **사라져 재기동 시 드라이버를 잃는다**.

### 변경
- **`provision.json` v1.1→v1.2** — `config_merge` 신설 (boolean, 기본 false)
  - `true` = 기존 설정에 **deep merge**, `false`(기본) = 통째로 교체(기존 동작 그대로)
  - 조건부 필수키: `config_merge=true` 면 `config` 는 부분 문서(`ven_id` 만) / 아니면 기존대로 `kind`·`backend` 필수. `if/then/else` 로 표현 — `allOf` 는 conjunctive 라 완화가 안 된다
  - 병합 기준(기존 설정)이 없는 엣지에는 적용 불가 — 수신측이 거부해야 한다(반쪽 설정을 쓰느니 명시적 실패)

### cascade
`gen_constants --all` 8 대상 (값 변경 없음).

### consumer 후속
- **edge-agent**: `config_merge=true` 수신 시 기존 YAML 과 deep merge 후 저장·적용, 기준 부재 시 거부
- **mgcc**: 단일 축 하달을 merge 로 발행

---

## 0.3.26 — 2026-07-31 MGCC 설정 평면 — authority 축 + microgrid 설정 채널 (additive = minor)

MGCC(마이크로그리드 중앙 컨트롤러)는 그룹 **발령**만 할 수 있고 멤버 엣지의 **설정**을 하달·회수할 수 없었다. 엣지엔 이미 자리가 있었는데(`config_lock.ConfigSource.MGCC=20`, 현장 운영자 > MGCC > GB > 자동) 계약이 두 가지를 막고 있었다.

**막고 있던 것 ① — 권한 축 부재**: `provision.source` 는 발행 *경로*(xlsx_upload/ui_edit/api/bulk_replay)이지 *권한*이 아니다. ConfigSource 별칭과 교집합이 0 이라, 엣지는 provision 으로 온 설정을 **무조건 GB(10)로 강등**해 왔다(edge `main.py` F2 판정 주석). MGCC 가 `source: "mgcc"` 를 보내도 GB 로 취급된다.

**막고 있던 것 ② — 슬롯 공유**: `fleet/provision/{ven_id}` 는 VEN 당 retained 슬롯 1개다. GB 와 MGCC 가 같이 쓰면 서로의 설정을 덮어쓰고, 엣지 `revision` 단조성(슬롯 단위)이 충돌해 한쪽 개정이 조용히 reject 된다 — 발령 축 분리 P1-1 과 **동형 사고**.

### 변경
- **`provision.json` v1.0→v1.1** — `authority` 필드 신설 (`auto|gb|mgcc`, 기본 `gb` = 하위호환)
  - `source`(경로)와 **다른 축**. edge `ConfigSource` 와 lock-step: auto=0 / gb=10 / mgcc=20
  - ⚠ `field_operator`(30)는 **enum 에서 제외** — 원격 채널이 현장 권한을 참칭하면 해제 경로가 사라져 MGCC 안전 설정을 영구 차단할 수 있다(edge F1 판정 계승)
  - `_consumers += mgcc`
- **`mqtt_topics.json` v1.2→v1.3**
  - `microgrid/provision/{ven_id}` 신설 (pub=**mgcc**, sub=edge-agent, retained) — GB 슬롯과 분리
  - `microgrid/provision_ack/{ven_id}` 신설 (pub=edge-agent, sub=**mgcc**) — 발행자별 응답 분리
  - `fleet/register/{ven_id}` subscriber += mgcc (연결 신청 수신)
  - `fleet/heartbeat/{ven_id}` subscriber += mgcc (생존 판정)
  - `gridbridge/dispatch_ack/…` subscriber += mgcc (이미 구독 중이던 사실의 선언 반영)
- `edge_registration.json`·`dispatch_ack.json` — `_consumers += mgcc`

### cascade
`gen_constants.py --all` 8 대상 regen (edge-agent·gridbridge·be-3d py/ts·agentleague·eduarena·8.simulation·ingestion-worker). 값 변경 없음 — 토픽 표·consumer 목록만.

### consumer 후속
- **edge-agent**: `microgrid/provision/+` 구독 + `payload.authority` → ConfigSource 판정(원격은 MGCC 상한 clamp) + `microgrid/provision_ack` 발행
- **mgcc**: provision 발행자 구현(revision 단조·ack 회수), `fleet/register` 승인 큐

---

## 0.3.25 — 2026-07-31 dispatch_ack 계약 신설 (정산 오귀속 루프 폐쇄, additive = minor)

`gridbridge/dispatch_ack/{event_id}/{ven_id}` 는 토픽만 선언돼 있고 **payload 계약이 없었으며, Edge 가 발행조차 하지 않았다**(발령이 completed 로 전이되지 않음). 그 결과 D7(정산 오귀속)의 생산자가 부재했다 — GB 는 MG 발령분을 알 방법이 없어 DR 실적으로 이중계상했다.

### 변경
- **`dispatch_ack.json` 신설** (`_usage: runtime-validate`, consumers = edge-agent·gridbridge)
  - `status` = `applied|rejected|expired|unsupported` — 게이트 거부·만료를 **정직하게** 구분
  - **`settlement_track`** = `gb_settlement|measured` (edge `SettlementTrack` lock-step) — 정산 귀속 축
  - `reduction_kw` = Edge **자기보고** 감축량. `_security` 에 "GB 는 정산 반영 전 telemetry_history 와 교차 검증(단독 신뢰 금지)" 명시
  - `interlocks[]`·`setpoint_c` — 요청과 실제 적용의 차이를 보고
- `mqtt_topics.json` v1.1→v1.2 — dispatch_ack 토픽에 `payload_schema` 연결
- `_index.yaml` 등재

### cascade
`gen_constants --all` regen(SOURCE_HASH). **KR canonical 값 불변.** pin lockstep v0.3.24→v0.3.25.

## 0.3.24 — 2026-07-31 microgrid 네임스페이스 분리 + 텔레메트리 provenance (전부 additive = minor)

Edge 개념 축 분리 판정(edge-agent `docs/ANALYSIS-EDGE-CONCEPT-AXES.md`) 의 계약 반영분.
사용자 결정: "노드는 쪼개지 말고 축을 쪼갠다 — 최대한 확장성 있게".

### 변경 (mqtt_topics.json v1.0→v1.1)
- **`microgrid` 네임스페이스 신설** + **`microgrid/dispatch/{event_id}`** (publisher=**mgcc**, subscriber=edge-agent, retained). MGCC 그리드 안전 발령 전용 축.
  - 이전엔 MGCC 가 `gridbridge/dispatch/{event_id}`(선언상 publisher=gridbridge **단독**)에 미선언 발행자로 끼어들었고, event_id 공간을 공유해 **retained 슬롯을 상호 덮어썼다**. 구독자는 payload `source` 문자열 하나로만 출처를 구분.
  - 전환 기간: edge-agent 는 두 토픽 모두 구독(event_id dedup 보유) → **무중단 컷오버**.
- `_consumers += mgcc` (MGCC 독립 repo 승격 2026-07-31 반영).

### 변경 (telemetry.json v1.2→v1.3, 필드 추가 = minor, required 불변)
- **`data_source`** optional 신설 — `measured|simulated|synthetic`. 값 정본 = `data_sources.json DATA_SOURCES`.
  - **왜**: 합성 데이터가 실측과 **동일 스키마·동일 토픽**으로 흘러 정산·학습 파이프라인이 구분할 수 없었다. 구분하려면 `fleet/register` 의 `edge_type` 을 별도 join 해야 했고 그건 노드 단위라 점별 혼합을 표현 못 한다.
  - 미제공 = "미상". 소비단은 **실측으로 가정 금지**.
- **`data_source_detail`** optional — 엣지 backend 정밀 표기(`virtual|replay|energyplus|real_bas`). replay 는 실측이나 **연도 시프트 재생**이라 measured 와 구분이 필요할 때.

### cascade
- `gen_constants --all` regen (SOURCE_HASH bump). **KR canonical 값 불변** — 신규 키 추가만.
- pin lockstep: edge-agent·gridbridge·be-3d `v0.3.23`→`v0.3.24` + 각 `ssot-drift.yml` ref 동반(`bump_ec_pin.py` 자동).

## 0.3.23 — 2026-07-31 equipment_taxonomy 신설 + opmode_strategy_map + port_allocation v1.2.0 + TW 碳費 (전부 additive = minor)

v0.3.22 이후 master 에 누적된 8 커밋을 태그로 확정. **consumer 가 이미 regen 한 생성본(`OPMODE_STRATEGY_MAP`·`EQUIPMENT_*`)이 태그에 없어 `ssot-drift` CI 가 6 PR 연속 실패**하던 pin skew 를 해소하는 릴리스.

### 변경 (schemas)
- **`equipment_taxonomy.json` 신설** — 설비 종류·동작·capability SSOT 정본. bems-console(저작)·edge-agent(수신·검증) 양측이 손코딩 대신 생성본 파생. codegen 진입.
- **`ems_strategies.json` += `opmode_strategy_map`** — BEMS 스케줄 구간 OpMode(`occupied`/`night`/`weekend`/`peak`/`emergency`) → M-code. console 주간 스케줄 저작 → edge `ScheduleRunner` 실행의 의미매핑 정본(edge-agent DEFERRED 해소 근거).
- **`port_allocation.json` v1.1.0→v1.2.0** — 실 포트 등재(8032 Exaone 등) + `agents`→`ingestion-worker` repo rename 반영.
- **`market_prices.json` += `carbon_fee_by_region`** — 대만 탄소비(碳費, 氣候變遷因應法, TWD/tCO2e). KR canonical(kau) 불변 = additive.
- **`patterns/viz_hints.json` + `scripts/gen_viz_hints.py`** — viz_hint 정규식 scoped codegen SSOT.

### cascade
- `gen_constants.py --all` regen 필요(SOURCE_HASH bump) — **KR canonical 값 불변**(배출계수·PE·ZEB·요금 전부 무변경, 신규 키 추가만).
- EC pin lockstep 3 consumer(edge-agent·gridbridge·building-energy-3d) pin `v0.3.22`→`v0.3.23` + 각 repo `ssot-drift.yml` 의 EC checkout `ref:` 동반 갱신(`bump_ec_pin.py` 가 이번 릴리스부터 자동 처리).
- corpus(`corpus/`): shared query corpus + combo·scenario suite 추가(5→7). 스키마 무관, 소비 repo 영향 0.

---

## 0.3.22 — 2026-07-25 TW 台電 시간대별 요금 additive (필드 추가 = minor) *(소급 기록)*

- **`market_prices.json` += `electricity_tariff_by_region.TW`** — 대만 台電 시간대별 요금(TWD, off/mid/peak + peak_hours). KR 요금 불변 = additive.
- 태그 릴리스 시 CHANGELOG 항목이 누락되어 0.3.23 릴리스에서 소급 기록.

---

## 0.3.21 — 2026-07-25 telemetry CanonicalPointAddress(CPA) $def + zones.point_id (필드 추가 = minor)

### 변경 (telemetry.json v1.1→v1.2, 필드 추가 = minor, 하위호환)
- **`$defs.CanonicalPointAddress` 신설** — 정규 관제점 주소 `{country}.{site}.{domain}.{equip}.{point}`(pattern). bems-console `lib/point-address` 정본. 노드 SSOT=ven_id·필지=pnu 는 별도(익명 site 파생).
- **`zones[].point_id` optional 추가** — 존의 CPA 앵커. required 불변(`["zone_id"]`)=하위호환, 미제공 시 소비단이 zone_id 로 파생.

### cascade
- telemetry.json = runtime-validate(비 codegen 입력) → **gen_constants drift 0**(8 consumer 전수 확인), consumer regen 불요. pydantic `_pydantic_models/telemetry.py` 재생성(위생). `validate_ssot --check all` 통과.
- consumer: edge-agent/gridbridge(런타임 소비, 코드변경 불요), bems-console(`ZoneTelemetry.point_id?` 소비). CPA blast radius = EC+bems only(사냥꾼 조사 확정).

---

## 0.3.20 — 2026-07-21 MGCC operating_mode 4번째 modality (§5.5) + setpoint required 결함 수정

### 변경 (dr_dispatch_event.json v1.2→v1.3, 필드 추가 = minor)
- **`OperatingModeCommand` $defs 신설** — `{profile(ObjectiveType 4종), enforce}`. MG(MGCC)가 엣지 APE 운영 프로파일을 **상시 설정**(§5.5, MG 적극성). 일회성 액션(target/setpoint/peak)과 달리 해제까지 지속되는 정책. 정산 무관(mandatory=false).
- **`DispatchCommand` oneOf += operating_mode** — 4번째 modality. producer=**MGCC**(GB 아님 — GB는 생성·소비 무관), consumer=edge-agent(APE persona 갱신).
- **`_consumers += mgcc`** — MGCC(신규 repo `projects/mgcc/`, :8070)가 dr_dispatch_event producer 로 등재. R18 당시 mock 이라 미등재였던 것.
- **결함 수정 (R18 command oneOf 도입 시 누락)**: top-level `required` 에서 `target_kw` 제거 → `allOf.if(command 없음).then(target_kw required)` 조건부로 전환. **기존 setpoint_command 이벤트가 target_kw required 로 거부되던 결함** 동반 수정(operating_mode·setpoint 모두 command 만으로 유효).

### cascade
- gen_constants --all 재생성(SOURCE_HASH drift 0). consumer pin-lockstep bump(v0.3.19→v0.3.20) 별도 흐름.
- mgcc 는 schema consumer(계약 준수)이나 codegen 상수 미소비(dict 조립) → PROJECT_TARGETS 미등록(파급 최소).

---

## 0.3.19 — 2026-07-21 R18 APE cross-repo 경계 — ems_strategies/dr_dispatch_event/edge_registration + tariff/ppa 신규

### 변경 (codegen 진입 — 상수 캐스케이드 O, pin lockstep bump 필수)
- **`ems_strategies.json` v3.0→v3.1** (R18 Item 1):
  - `$defs/ObjectiveType` 신설 = `{reliability, economic, carbon, optimal}` — objective 축 단일 SSOT.
    dr_dispatch_event.DispatchSource 가 이 값집합을 재사용(∪ microgrid_safety), `signal_mapping_dr` /
    `persona_strategy_map` objective 키도 이 enum 과 lock-step.
  - `signal_mapping_dr` 2 objective→4 objective 확장 (8키→16키). 신규 `carbon`/`optimal` 누락 시
    `reliability` 보수 fallback (description 명문화). `$defs/SignalDrMapping` 로 추출.
  - `persona_strategy_map` 신설 — APE 운영 프로파일(objective)→{상시 M-code, 피크 M-code, ess_reserve_pct 0~100}.
    M-code = `StrategyCode $ref` 재사용(손코딩 금지). `$defs/PersonaStrategy`.
  - 신규 상수: `OBJECTIVE_TYPES`(전 consumer), `PERSONA_STRATEGY_MAP`(edge-agent·be-3d).
- **`dr_dispatch_event.json` v1.1→v1.2** (R18 Item 3):
  - `DispatchSource` enum 2종→5종 = ObjectiveType ∪ {microgrid_safety}. 하위호환(기존 producer 는 2종만 emit).
  - `command` (선택) 추가 = `$defs/DispatchCommand` oneOf(`target_kw` | `setpoint_command` | `peak_limit_kw`).
    **GB 정산 경계**: target_kw·peak_limit_kw = GB settlement 대상 / setpoint_command = Edge 직접제어
    (GB measured passthrough, `mandatory=false` 필수 — Edge A-6 수신검증). top-level `target_kw` 필수 유지(하위호환).
  - `MemberAllocation` += `setpoint_c`(optional, 설정온도 경로). `allocated_kw=0` 병기 허용.
- **`edge_registration.json` v1.1→v1.2** (R18 Item 2):
  - `affiliations[]` 다형 추가 = `[{type: esg|microgrid|independent, id}]`. 다중 소속(ESG+microgrid) 지원.
    `group_id` = DEPRECATED(하위호환 유지 — 구형 페이로드는 GB 가 `affiliations[{type:esg, id:group_id}]` 로 자동 마이그레이션).
    microgrid = Edge 실행 컨텍스트(GB 정산 무연동, esg 만 esg_group_venues 반영).
  - `_consumers += gridbridge` (GB `_handle_register` 가 fleet/register 소비 — 메타 반영).

### 신규 (reference-only — gen_constants 미진입, GB `_consumers` 미포함)
- **`tariff_contract.json` v1.0** (R18 Item 4): KEPCO 고압 요금(계약전력·기본요금 고압A/B I/II/III·TOU).
  `contract_id` required(콘솔 tariffContractId 참조키). `_consumers=[edge-agent, building-energy-3d]`.
- **`ppa_contract.json` v1.0** (R18 Item 4): PPA(단가·탄소계수·take-or-pay). `contract_id` required(콘솔 ppaContractId 참조키).
  `_consumers=[edge-agent, building-energy-3d]`. canonical 값 = 생성본 import(손편집 금지).

### 가드
- `validate_ssot.check_objective_dispatch_sync` 신설 — ObjectiveType↔DispatchSource enum + signal_mapping_dr/
  persona_strategy_map objective 키 lock-step 강제(별도 인라인 enum drift 차단).
- `_index.yaml` += TariffContract·PpaContract (전수 등재 게이트).
- **pin lockstep**: edge-agent·gridbridge·building-energy-3d `pyproject.toml` @v0.3.19 bump + `--all` regen (SOURCE_HASH 캐스케이드).

---

## 0.3.18 — 2026-07-20 telemetry.json v1.0→v1.1 존별 세부 텔레메트리(zones[]) 추가

### 변경 (runtime-validate schema — gen_constants 미진입, 상수 캐스케이드 없음)
- **`telemetry.json` v1.0→v1.1**: `properties.zones` (선택 배열) 추가 — 존/포인트 단위 계측
  가능 장치가 존별 세부값을 방출. item = `{zone_id(필수), indoor_temp_c, hvac_setpoint_c,
  co2_ppm, humidity_pct, occupancy, power_kw}`. **하위 호환**(필드 추가 = minor): 미지원 장치는
  생략(건물 집계값만), 미지원 수신자(구 pin consumer)는 무시(forward-compat, `additionalProperties`
  미제한). `zone_id` = 콘솔 공간 IR `zone.id` / BAS 모델 `zone.id` 매핑 키 — 매핑 시 콘솔이
  존 provenance 를 estimate ◐→measured ● 승격.
- **동기**: bems-console 공간축 라이브 바인딩 — 기존 venue-level 텔레메트리는 건물당 값 1개씩이라
  존별 measured 승격 불가였음. 본 필드가 그 데이터 통로.
- **소비**: edge-agent(방출 — E+ 드라이버 존별 온도) / gridbridge(passthrough 검증) / bems-console(승격 소비).
  telemetry = runtime-validate(gen_constants 미진입) → 상수 SOURCE_HASH 캐스케이드 없음.
  pin lockstep = edge-agent · gridbridge `pyproject.toml` @v0.3.18 bump.

## 0.3.8 — 2026-06-17 policy_measures.json 신설 + Objective enum 등재 (AgentLeague debate SSOT 승격)

### 변경 (reference-only schema — gen 미진입, hash cascade 없음)
- **신규 `schemas/policy_measures.json`** (reference-only, v1.0): MeasureCode 카탈로그 SSOT —
  운영 EMS(ems_strategies.json#StrategyCode M00~M20)가 표현 못 하는 **자본·설계 조치** 8종
  (ENV01~03 외피·창호 retrofit / PV01~02 신재생 생성 / SRC01~02 열원 전환 / MAT01 저탄소 자재).
  `$defs.MeasureCode`(8) + `$defs.MeasureMetric`(operational_kwh/self_sufficiency/primary_energy/
  embodied_carbon) + measure 별 `{name, metric, base, eplus_ref, note}`. `eplus_ref` 보존 =
  SIM E+ 정밀화(ems_transformer) 입력. AgentLeague `backend/modules/debate/policy_levers.py#
  POLICY_MEASURES` 비공식 원본을 정식 SSOT 로 승격. _consumers = agentleague / ems_transformer /
  building-energy-3d. **코드 prefix 3+ 문자(ENV/PV/SRC/MAT) 의무** — 단일문자 E?/S? 는
  `legacy_ems_code_mapping.json#drift_guard` 가 deprecated 로 차단(애초 명명 이유).
- **`policy_evaluation_contract.json` v1.0→v1.1**: `$defs.Objective` enum 추가
  (carbon_tco2 / primary_energy / roi_payback / equity_weighted / peak_shift). F14 평가 목적함수
  재사용 어휘 — AgentLeague `policy_levers.py#OBJECTIVES` 원본 승격. lever→objective 매핑은
  agentleague debate 전용이라 SSOT 비대상(어휘만 공유).
- **`_index.yaml`**: `PolicyMeasures` 등재 + 카탈로그 카운트 58→59.
- **소비**: 3 consumer 는 wheel `load_schema("policy_measures")` / `load_schema("policy_evaluation_contract")`.
  reference-only 라 gen_constants 미진입 → 6-repo SOURCE_HASH 캐스케이드 없음(EC + 3 consumer 4-repo 한정).
- **follow-up(범위 밖)**: agentleague/ems inline POLICY_MEASURES·OBJECTIVES → SSOT 참조 교체는 consumer-side.

---

## 0.3.7 — 2026-06-17 CarbonCritic overclaim 게이트 (self-reference 독립화, P2-c)

### 변경 (schema 무관 — hash cascade 없음)
- **`critics/c_carbon.py`**: `CarbonCritic.review` 에 과대주장(overclaim) 게이트 추가 (additive).
  `context["claimed_reduction_pct"]`(에이전트/LLM 주장) > `context["known_rate"]`(독립 ground
  truth)×1.25 → `rule="overclaim"` 위반. `claimed > 0.5` → `rule="implausible_reduction"`.
- **self-reference 죽은 게이트 방지**: claimed/known 은 context 의 **별개 키에서만** 읽고,
  `known_rate` 부재(None)/0 시 claimed 로 대체하지 않고 검사 skip(`_as_rate` → None 구분).
  W4 실 Critic 스왑(`AGENTLEAGUE_REAL_CRITICS=1`) 시 미러와 동일하게 게이트가 살아있음.
- **backward-compatible**: context 없는 기존 호출(DR `critics/gate.py` 등)은 overclaim 무관 — 회귀 0.
- 신규 단위 5 (overclaim 발화/임계내 무발화/known부재 skip/implausible/무context). 정본:
  `agentleague/docs/POLICY_LEVER_SOLVABILITY_AUDIT.md` §6 P2-c / CB-01.

---

## 0.3.6 — 2026-06-08 Deferred D-3 — 20 BASE CORE_KEYWORDS 로컬 검증 (mirror lock-step)

### 변경 (schema 무관 — hash cascade 없음)
- **CLAUDE.md**: mirror 헤더에 `MIRROR_CORE_KEYWORDS_BASE_V1` enumeration 블록 신설 —
  20 BASE CORE_KEYWORDS 를 명시(`G-PE1`…`tenant_regions.json`). 기존엔 "20 CORE_KEYWORDS" 라고만
  선언하고 토큰 enumeration 이 본 repo 에 없어 로컬 검증 불가였다(D-3).
- **신규 가드** `validate_ssot.check_mirror_core_keywords()` — enumeration 토큰이 정확히 20 개이고,
  각 토큰이 mirror 헤더 본문(enumeration 제외)에 전수 등장하는지 로컬 검증. prose stale 검출.
- **lock-step (sibling)**: ai-champion-2026 `verify_cross_folder_mirror_drift.py` 에
  `check_energy_contracts_enumeration()` 추가 — 본 enumeration ↔ `BASE_KEYWORDS` 동일 집합 강제
  (enumeration drift 차단). 별 repo PR.

## 0.3.5 — 2026-06-08 Deferred D-1/D-2 coordinated bump (사냥꾼 M4/M7 cross-folder 해소)

### 변경 (schema — hash cascade)
- **D-1 (M4)**: `esg_policy.json` · `dr_dispatch_event.json` `_usage` `runtime-validate` → **`hybrid`**.
  두 schema 는 `gen_constants.load_schemas()` 의 codegen 입력(DR_TYPES/DISPATCH_* 등)인데
  `runtime-validate` 로 오분류돼 있었다.
- **D-2 (M7)**: `ems_strategies.json#default.legacy_mapping.gcs_e_codes` 5건 정정 —
  정본 `legacy_ems_code_mapping.json#deprecated_e_codes` 와 일치:
  `E1` M01→**M06**, `E2` M06→**M01**, `E7` M05→**M04**, `E10` M14→**M11**, `E11` M15→**M12**.

### 신규 가드 (validate_ssot.py)
- `check_codegen_input_usage()` — 역방향: `load_schemas()` 가 로드하는 schema 는
  `_usage ∈ {codegen, hybrid}` 강제 (정방향 `check_schema_usage_headers` 의 사각 보완).
- `check_legacy_code_consistency()` — `ems_strategies.gcs_e_codes` ↔
  `legacy_ems_code_mapping.deprecated_e_codes.maps_to` 교차 정합.

### Cascade
- 6 consumer `_generated_constants.{py,ts}` SOURCE_HASH `f462482943b38ce1` → `05d50c0601204d89`.
  Python consumer 는 `LEGACY_MAPPING.gcs_e_codes` 5건 동시 정정. TS 는 hash 만(LEGACY_MAPPING 미export).
- consumer SSOT 테스트: edge-agent 20 / gridbridge 13 / be-3d 27 PASS.
  eduarena 는 본 regen 이 기존 drift(`test_gen_constants_check_passes`) 1건 정정(4→3),
  잔여 3건은 pre-existing(Phase C stale 경로 + JWT, 본 변경 무관).

---

## 0.2.3 — 2026-05-27 gen_constants TS critic enum (frontend MEDIUM — i18n / UI 매핑)

### 변경
- `scripts/gen_constants.py` `gen_typescript()` 에 critics 블록 추가
- 6 consumer `_generated_constants.{py,ts}` SOURCE_HASH cascade (drift 0)
- be-3d ts exports 화이트리스트에 critic 심볼 7 추가:
  - `CRITIC_NAMES` / `CRITIC_LABEL_KO`
  - `VERDICT_VALUES` / `VERDICT_LABEL_KO`
  - `GATE_DECISIONS` / `JUDGE_DECISIONS`
  - `DR_MANDATORY_SIGNAL_LEVELS`

### 사유
- 사냥꾼 frontend MEDIUM: `Verdict.PASS/WARN/FAIL` 값과 critic name (`c_legal` 등) 이
  frontend TypeScript 측에 자동 생성되지 않아 UI 가 문자열 하드코딩 → drift 위험
- 한국어 라벨 (`VERDICT_LABEL_KO`, `CRITIC_LABEL_KO`) 도 함께 노출 — i18n catalog override 가능

### 호환성
- additive only — 기존 TS export 보존
- non-be-3d consumer 는 SOURCE_HASH cascade 효과만 (실 export 없음)

---

## 0.2.2 — 2026-05-27 critics Pydantic mirrors (frontend HIGH — OpenAPI 노출)

### 신규
- `energy_contracts/critics/_pydantic_models.py` — FastAPI OpenAPI 자동 생성용 Pydantic v2 mirrors
  - `Violation` (rule + extras allowed)
  - `CriticResultModel` (critic / verdict Literal / score / violations / notes)
  - `GateVerdictModel` (decision Literal / results / cache_hit)
  - `BatchDebateVerdictModel` (judge_decision Literal / realtime_results / carbon_result | None / notes)
  - `BatchDebateResponse` extends VerdictModel + event_id + n_participating_venues + source Literal | None
  - `CriticsBlockDetail` (reason / decision / results / remediation_key / remediation)
- `energy_contracts.critics` 에서 모두 re-export — 컨슈머는 `from energy_contracts.critics import BatchDebateResponse` 한 줄

### 사유
- 사냥꾼 frontend HIGH 보고: 기존 dataclass (GateVerdict/CriticResult) 만으로는 FastAPI 가 OpenAPI schema 생성 불가 → `/openapi.json` 에 untyped dict
- GB `debate.py` + be-3d `dr_dispatch.py` 가 `response_model=BatchDebateResponse` 선언 가능, schema cascade

### 호환성
- 기존 dataclass 보존 — 내부 SSOT 캐리어로 그대로 사용
- Pydantic 은 FastAPI 응답 / 클라이언트 검증 / OpenAPI 노출만 담당
- breaking 변경 없음

---

## 0.2.1 — 2026-05-27 critics 사냥꾼 patch (M2 false-pass 방지 + M3 mandatory SSOT)

### 변경 (semantic)
- `CriticsGate.evaluate_batch_debate()` — outcome=None 시 Carbon Critic skip.
  사유: dispatch event 만으로는 배출계수 컨텍스트 결핍 → 거의 항상 false-pass.
  이전 동작: `carbon_result=CriticResult(verdict=PASS)` 항상 포함.
  신규 동작: `carbon_result=None`, `notes="outcome 미주입 — Carbon skip"`.
  judge_decision 은 realtime 3 종 만으로 산출.
  → 사후 batch debate 호출자는 outcome 주입을 적극 권장.

### 신규 export
- `energy_contracts.critics.MANDATORY_SIGNAL_LEVELS = frozenset({"HIGH", "EMERGENCY"})`
  사유: GB local `_MANDATORY_SIGNALS` 분리 → SSOT drift 위험 (M3). EC 가 SSOT.

### 호환성
- `BatchDebateVerdict.carbon_result` 가 `CriticResult | None` 으로 type 완화
  (이전: 항상 non-None). UI 컨슈머는 None 체크 추가 필요 — Layer 5 mock 카르테는
  아직 carbon_result 사용 안 함, 영향 없음.

### 회귀
- EC tests 19 PASS (1 신규 outcome=None skip)
- GB tests 10 PASS (1 신규 outcome 주입 케이스)

---

## 0.2.0 — 2026-05-27 critics 패키지 신설 (SSOT_GOVERNANCE §9 도메인 횡단 분리)

### 신규
- `energy_contracts/critics/` — 4 종 Critic + CriticsGate 조합자 (도메인 중립 SSOT)
  - `critic_base.py` — Critic ABC + CriticResult + Verdict (PASS/WARN/FAIL)
  - `c_legal.py`    — 법령 인용 정확성 (`rules/legal-citation.md`)
  - `c_carbon.py`   — 배출계수 SSOT 정합 (`CARBON_EMISSION_FACTORS.yaml`)
  - `c_safety.py`   — HVAC/PMV/ESS/조명 interlock
  - `c_data.py`     — NDA 출처 fingerprint (`rules/private-data-disclosure.md`, zero-tolerance)
  - `gate.py`       — CriticsGate (실시간 3 종 + 사후 batch debate 4 종) + summarize_dispatch_for_critics
- `tests/test_critics.py` — 5 test (clean 90% 통과 + violation 80% 검출 + zero-tolerance + serialize)
- `tests/test_critics_gate.py` — 13 test (summary builder + realtime gate + cache + batch debate)
- `__version__` 0.1.0 → 0.2.0, `pyproject.toml` 동일

### 이동 (be-3d → EC)
- `building-energy-3d/src/critics/` → `energy_contracts/critics/` (5 파일)
- `building-energy-3d/src/agents/dr/critics_gate.py` → `energy_contracts/critics/gate.py`
- `building-energy-3d/tests/test_critics.py` → `tests/test_critics.py`
- `building-energy-3d/tests/unit/dr/test_critics_gate.py` → `tests/test_critics_gate.py`

### SSOT 거버넌스
- `myjob/docs/SSOT_GOVERNANCE.md` §9 신규 — 도메인 횡단 로직 분리 원칙 (3 계층 책임 분리 + Q1~Q4 진입 판정 + DR Critics 사례)
- 영향 repo (lockstep release): be-3d (import 마이그), gridbridge (신규 realtime owner wire-up)

### 회귀
- EC critics tests 18/18 PASS

---

## (unversioned) — 2026-05-25 security_policy.json v1.1 (CSP 강화, P6 SSOT cascade)

### 변경
- `security_policy.json` `default.headers.Content-Security-Policy`:
  - `script-src` 에서 `'unsafe-eval'` 제거
  - `style-src` 에서 `'unsafe-inline'` 제거
- `version` 1.0 → 1.1, `updated` 2026-05-25
- be-3d CSP P5 #A~#D 완료 (2026-05-25, be-3d `bb72f51`) 반영
- Cesium 의존 페이지(`vworld.html`/`cesium.html`) 와 legacy simulator iframe(`/simulators/*`)은 be-3d nginx location 에서 개별 완화 — SSOT default 와 별개

### 영향
- 6 consumer `_generated_constants.{py,ts}` cascade — `gen_constants.py --all` 실행, drift 0 확인
  - `building-energy-3d/src/shared/_generated_constants.py`
  - `building-energy-3d/frontend/src/shared/_generated_constants.ts` (security 미포함 — exports 화이트리스트)
  - `gridbridge/src/_generated_constants.py`
  - `edge-agent/src/_generated_constants.py`
  - `agentleague/backend/_generated_constants.py`
  - `eduarena/backend/_generated_constants.py`
- be-3d FastAPI `SecurityHeadersMiddleware` + gridbridge `main.py` + agentleague `main.py` 가 SSOT 직접 import — 재빌드/재시작 시 신규 CSP 자동 적용 (API JSON 응답에만 영향, nginx 가 서빙하는 HTML 은 nginx CSP 사용)
- 회귀: gridbridge 290 PASS, be-3d SSOT consistency 26 PASS (1 pre-existing path bug 무관)

---

## 0.1.0 — 2026-05-19 패키지화 + wheel 배포 (Phase C, agents a12)

### 추가
- `pyproject.toml` — setuptools 기반 패키지 정의 (`requires-python = ">=3.11"`)
- `energy_contracts/__init__.py` — `load_schema()`, `list_schemas()`, `SCHEMAS_DIR` 헬퍼
- `energy_contracts/_pydantic_models/__init__.py` — 서브패키지 진입점
- wheel: `dist/energy_contracts-0.1.0-py3-none-any.whl` (52 schemas + 2 models + dist-info, 59 files)

### 이동 (R, 57 파일)
- `schemas/*.json` → `energy_contracts/schemas/*.json` — wheel package data 로 포함
- `scripts/_pydantic_models/*.py` → `energy_contracts/_pydantic_models/*.py`

### 도구 path 갱신 (`SCHEMAS_DIR`)
- `scripts/gen_constants.py:30` — `CONTRACTS_ROOT / "energy_contracts" / "schemas"`
- `scripts/validate_ssot.py:33` — 동일
- `scripts/gen_pydantic_models.py:19-20` — `SCHEMAS_DIR` + `OUT_DIR` 모두 `energy_contracts/` 하위
- `scripts/classify_tests.py:31` — `test_classification.json` 경로 갱신

### 호환성
- 5 consumer repo `_generated_constants.{py,ts}` SOURCE_HASH 동기화 유지 (드리프트 없음, `validate_ssot.py` 통과)
- 기존 `python energy-contracts/scripts/gen_constants.py --all` 진입점 그대로 (내부 path 만 변경)
- agents repo 가 `pip install -e ../energy-contracts` 또는 wheel 로 import 검증 ✅ (agents `.venv` Py 3.11.9 + be-3d `venv` Py 3.13.3 모두 통과)

---

## (unversioned) — 2026-05-18 H11 cross-platform hash fix + TD-9 단위 테스트

### gen_constants.py 버그 수정
- `schemas_hash()` 가 `read_bytes()` 로 self-bytes 를 읽어 Windows(CRLF) / Linux(LF) 에서 hash 가 달랐음 → CI 서버측 검증에서 false-positive DRIFT 발생
- Fix: `read_text(encoding="utf-8").encode("utf-8")` 로 newline 정규화 (PR #2, `be3c75b`)
- SOURCE_HASH cascade: `58ff101d` → `1a793963` (5 consumer repo 6 파일 regen)

### 신규 단위 테스트 (TD-9, PR #3)
- `tests/test_classify_tests.py` — `_strip_headerless_pytestmark` 4 케이스 (canonical_only / raw_only / **H1 회귀 canonical+raw** / dangling import)
- pytest 4/4 PASS (0.23s)

### 서버측 SSOT pre-merge gate (H11)
- 5 consumer repo (edge-agent / gridbridge / agentleague / eduarena / building-energy-3d) 에 `.github/workflows/ssot-drift.yml` 추가
- PR/push 시 energy-contracts master 와 `_generated_constants.*` drift 자동 검출 (서버측 강제, `--no-verify` 우회 차단)
- grep 필터로 자기 repo 외 sibling MISSING 무시

---

## v1.4.0 — 2026-04-23 (R16/R17 + VW forecast/anomaly + GB bulk sync)

### 개요
VW 에너지 예측(PatchTST 168→24h) + 이상탐지 API 및 GB ESG VEN 일괄 동기화 스키마 추가.
R16 Phase A 완료(5 VEN 실측 검증), R17 Item 1~5 RESOLVED.

### 신규 스키마
- `schemas/forecast_response.json` — PatchTST 168h→24h 예측 응답 (entity_id, model, forecast[24], metrics)
- `schemas/anomaly_response.json` — 이상탐지 응답 (z_score/isolation_forest/forecast_residual, status, score 0~1)
- `schemas/esg_venue_bulk_sync.json` — PUT /esg/groups/{id}/venues 요청·응답 (R14-8 BulkVenueSync)

### 리뷰 라운드 상태 갱신
- R16: Phase A 완료 (5 VEN × 실측 데이터 MQTT 적재 검증) · Phase B(168→24 예측), Phase C(이상탐지) 대기
- R17: Item 1~5 RESOLVED · Item 6(UI regression) ACK(중기)

---

## (unversioned) — 2026-04-21 라운드 9 Edge 응답

Edge 팀이 VW/GB 의 Tailscale 경로 제안(라운드 9) 에 일괄 답변. 스키마 변경 없음, REVIEW.md 만 갱신.

- R9-1 Tailscale 옵션 A **수락**
- R9-2 PoC 는 공용 Tailscale, 정식 운영은 Headscale (self-hosted) 선호
- R9-3 Docker `0.0.0.0:1883` + iptables (`tailscale0` only) 2중 방어
- R9-4 **R6-8 mTLS Phase D 강등 제안** — Tailscale 이 전송 암호화 + peer 인증 제공, ACL 은 Tailscale tag 로 대체
- R9-5 RPi 5 Tailscale 추정 30~50 MB · CPU <2% — `bench_rpi5.py` 에서 실측 예정
- 실행 단계 4 (RPi 5 Tailscale 설치) — Edge 담당 · RPi 5 실기 확보 대기

---

## v1.3.1 — 2026-04-20 (ARCH-R8-1 AUDIT-R2)

### 개요
Edge 감사 P1 반영. Edge·GB·VW 3계층에서 `commissioning_hash` 알고리즘이 드리프트할 위험 차단.

### 신규 프로토콜 문서
- `protocols/commissioning-hash.md` — `commissioning_hash` 알고리즘 SSOT. canonical JSON(`sort_keys=True, separators=(",",":"), ensure_ascii=False`) + UTF-8 + SHA-256. Edge/GB/VW 구현 모두 이 문서 참조 필수.

### 스키마 갱신
- `schemas/engineering_session.json` — `commissioning_hash.description` 에 알고리즘 SSOT 링크 명시.

---

## v1.3 — 2026-04-20 (R8-5)

### 개요
Edge Engineering/Monitoring 분리 + 22기술 번들·세션 저장. 라운드 8 VW/GB 합의 후 Edge 팀이 작성한 3 스키마 초안 + MQTT 토픽 2종. GB Tech Catalog Registry + Bundle Builder 구현 대기 (R8-2, 4주 공수).

### 신규 스키마
- `schemas/engineering_session.json` **v1.0** — 기사 설치 세션 (session_id, technician_id, selected_techs, provisioning_config $ref provision.json#/config, dry_run_result, commissioning_hash, previous_session_id). Edge seal 시 로컬 `sessions/*.yaml` + `fleet/engineering/{ven_id}` retain 발행.
- `schemas/engineering_diff.json` **v1.0** — 세션 간 변경 체인. techs_added/removed + config_changes (JSON Pointer 기반) + bundle_version_change. Edge `fleet/engineering_diff/{ven_id}` 발행, GB append-only 이력 저장.
- `schemas/bundle_manifest.json` **v1.0** — 22기술 번들 루트 manifest. version(semver), min_edge_schema, tech_list[](id, sha256, supported_backends, applicable_building_types), signature (ed25519). Edge A/B atomic swap + 서명 검증.

### 프로토콜 갱신
- `protocols/mqtt-topics.md`:
  - `fleet/engineering/{ven_id}` — Edge pub (QoS 1, retain=True) · GB+VW sub
  - `fleet/engineering_diff/{ven_id}` — Edge pub (QoS 1, retain=False) · GB+VW sub
  - ACL 예시 갱신 + mTLS Phase C cert subject 정책 명시

### VW/GB 합의 (라운드 8, `5d596d5`)
- Engineering/Monitoring 분리 + 3역할 권한 (R8-1)
- GB Tech Catalog Registry + Bundle Builder 4주 착수 (R8-2)
- 서명 키 GB 위탁, Edge 공개키 embed (R8-8)
- mTLS Phase C RPi 5 완료 후 (R8-9)
- Fleet 히트맵 VW 포털 관리자 탭 (R8-10)

### 참조
- Edge 설계: `edge-agent/docs/DESIGN-EDGE-ENGINEERING.md`
- Edge 로드맵: `edge-agent/docs/ROADMAP-R8.md`
- 감사: `edge-agent/docs/AUDIT-2026-04-20.md`

---

## v1.2 — 2026-04-19 (R6-2·R6-4·R6-10·R7-3)

### 개요
VW RFC-ESG-SETUP-WORKFLOW.md §5 "건축물대장 부정확" 문제 해결용 외피 스키마 신설 + 프로비저닝 채널 명세. 리뷰 라운드 6 대응. R7 응답 반영 (api_token_hash 추가).

### 신규 스키마
- `schemas/building_envelope.json` **v1.0** — 건물 외피·기하·설비 메타. `source_of_truth` (field/register/archetype) 우선순위, geometry(면적·층수·준공년도·방위·구조), envelope(U-value 4종·WWR·SHGC·VLT·기밀도), systems(HVAC·조명·기기부하·ESS·PV).
- `schemas/provision.json` **v1.0** — GB → Edge 프로비저닝 페이로드. provisioning_id(UUID) + revision(단조증가) + config(전체 Edge 설정) + apply_mode(hot_reload/restart_required/dry_run) + expected_config_hash.
- `schemas/provision_ack.json` **v1.0** — Edge → GB ack. applied/pending_restart/rejected/validated/hash_mismatch 상태 + actual_config_hash + reason + warnings.

### 갱신
- `edge_registration.json` — `envelope` 필드 추가 (building_envelope.json 참조).
- `edge_status.json` v1.2 — `config_hash` (16자리 hex) + `config_updated_at` + `api_token_hash` (R7-3, Edge 로컬 HTTP API 토큰 해시) 추가. VW 중앙 설정과 drift 감지 + 현장 토큰 드리프트 탐지.
- `protocols/mqtt-topics.md` — `fleet/provision/{ven_id}` (GB→Edge, QoS 2, Retain) + `fleet/provision_ack/{ven_id}` (Edge→GB) 추가. ACL 예시 갱신.

### 리뷰 연계
| 라운드 | 항목 | 해결 |
|:---:|------|:---:|
| R6 | R6-2 building_envelope.json 스키마 신설 | ✅ |
| R6 | R6-4 fleet/provision 토픽 + provision.json·provision_ack.json | ✅ (Edge 초안 — GB 수락 완료) |
| R6 | R6-10 edge_status.json config_hash | ✅ |
| R7 | R7-3 Edge 로컬 API 토큰 해시 heartbeat 포함 | ✅ (edge_status.json v1.2 api_token_hash) |

---

## v1.1 — 2026-04-19

### 개요
관측형(telemetry) vs 제어형(dispatch) 수용가 이분화. Edge 팀 스펙 4종 + 공용 enum SSOT 추가.

### 신규 스키마
- `schemas/venue.json` **v1.1** — 수용가 레지스트리. `kind × backend` 이원 분류.
- `schemas/virtual_prosumer.json` **v1.0** — E+ 가상 수용가 I/O 계약 (observable·controllable·step_seconds·real_time_factor).
- `schemas/control_response.json` **v1.0** — 제어 명령 적용 결과 (requested vs actual, interlocks).
- `schemas/edge_registration.json` **v1.1** — Edge 자동 등록 메타 (edge_type·location·ep_model·capabilities).
- `schemas/edge_status.json` **v1.0** — heartbeat + 드라이버별 연결 상태 + 큐 사이즈.
- `schemas/common.json` **v1.0** — 공용 enum·패턴 SSOT (Strategy·Kind·Backend·BuildingType·EdgeType·SignalLevel·VenId·VirtualPNU).

### 기존 스키마 갱신 (description 보강만, 호환성 유지)
- `control_command.json` — strategy description에 "common.json §Strategy SSOT 동기화" 명시. constraints 각 필드에 기본값 서술.
- `control_response.json` — strategy description에 "status=failed/rejected 시 생략 가능" 명시.
- `dr_event.json` — end_time description에 "CANCELLED 시 원래 예정 종료 시각 보존" 명시.

### 프로토콜
- `protocols/mqtt-topics.md` — Edge→GB 방향(control_response·registration·heartbeat) + fleet/register·fleet/heartbeat·fleet/{ven}/ota 토픽, ven_id 네이밍 정규식(5 접두), mosquitto ACL 예시(14 토픽), kind 라우팅 규칙.
- `protocols/broker-architecture.md` — VW 측 제안(Mosquitto/EMQX 단계·인증·Edge 3유형·ESG 그룹 4종·역할 분담). §9 TODO 7건 중 4건 완료 체크, 3건 Edge 제안 반영.

### 수용가 이분화 (CLAUDE.md)
- 관측형(`kind=telemetry`) — 편의점 220채 DB replay. `command/schedule` 발행 스킵.
- 제어형(`kind=dispatch`) — E+ 가상·실 BAS. 양방향.
- ESG 사전 정의 그룹 4종: `ESG-STORE-100`(100채), `ESG-STORE-120`(124채), `ESG-EP-OFFICE`, `ESG-EP-APT`.
- 가상 PNU: `99001xxxxx`=100그룹, `99002xxxxx`=120그룹.
- ven_id 접두: `VEN-STORE-·VEN-EP-·VEN-REAL-·VEN-TEST-·VEN-E2E-`.

### 리뷰 라운드
| 날짜 | 커밋 | 내용 |
|------|:---:|------|
| 2026-04-19 | `a60efee` | Edge측 스펙 4종 + 관측형/제어형 이분화 (v1.1 초안) |
| 2026-04-19 | `4db7f9a` | VW broker-architecture §5 예시·§3 ACL 정합 교정 + §9 TODO 응답 |
| 2026-04-19 | (이 커밋) | REVIEW.md HIGH 1 + MEDIUM 3 + LOW 2 반영 (common.json 신설, description 보강, CHANGELOG 신설) |

### 버전 동시 변경 관계

`edge_registration.json` v1.1 과 `venue.json` v1.1 은 동일 동기 — 수용가 분류체계(`kind`·`backend`)가 양쪽 모두에 나타나며 공용 SSOT(`common.json`)를 참조한다. 둘 중 하나만 bump 되는 변경은 금지.

---

## v1.0 — 2026-04-19

초기 릴리즈.

### 스키마
- `dr_event.json` — DR 이벤트 (GB 생성)
- `reduction_schedule.json` — 감축 스케줄 (VW/GB → Edge)
- `control_command.json` — 제어 명령 (VW/GB → Edge)
- `telemetry.json` — 텔레메트리 (Edge → GB/VW)

### 프로토콜
- `protocols/mqtt-topics.md` 초안
- 경로 0~4 정의 (사용자→VW, VW→GB→EA, VW→EA, EA→VW, EA→GB→VW)
