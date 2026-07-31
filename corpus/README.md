# 질의 코퍼스 (Query Corpus) — 모든 서브폴더 공유 회귀 테스트셋

> **한 줄**: "질의 / 시나리오 / compose / capability" 로 흩어진 테스트 대상을 **단일 공유 코퍼스**로 통일한다. 모델·opcode·라우팅·데이터 중 **무엇이 바뀌든 `run_corpus.py` 하나로 전수 재실행**.
>
> **위치 근거**: energy-contracts = Tier-2 SSOT 허브(`myjob/docs/SSOT_GOVERNANCE.md §9`). 이 코퍼스는 특정 앱(studio)의 것이 아니라 **AI 챔피언·lab·be-3d·studio·gateway 가 공유**하는 도메인 중립 자산 → `critics/`·`esg/`·`retry_policy/` 와 같은 자리(공유 허브).
>
> **설계 정본**: `energy-decision-studio/docs/QUERY_CORPUS_SSOT.md` (리서치 + 3층위 어휘 + 마이그레이션).

---

## 0. 이게 무슨 문제를 푸는가

같은 개념("사용자가 물을 수 있는 것")이 repo·시대별로 6곳 이상에 파편화돼 있고 **서로 파생 관계가 없다**. opcode 하나가 추가돼도 combo QC는 모르고, 96 op 중 대부분은 대표 질의가 없으며, 변경 시 사람이 `run_qc`/`gen_combo_qc`/`probe_*`/gateway 골든을 **각각 기억해서** 돌려야 했다.

이 코퍼스는 그 셋을 하나로 엮는다:
- **canonical source**(각 repo 소유, 손대지 않음)에서 **파생 병합** → `query_corpus.generated.json`
- 사람이 판단해야 하는 것(대표 질의·픽스처)만 `query_overlay.jsonc` 손작성
- 어느 서브폴더에서든 `run_corpus.py` 단일 진입점으로 전수 실행

---

## 1. 파일 구성

| 파일 | 역할 | 누가 고치나 |
|------|------|-----------|
| `query_overlay.jsonc` | **판단 층** — A/C opcode 대표질의(probeQuery)·capability 프로브·픽스처(대표 지역/건물/차원)·질의종류(C/S/L 24)·refuse 프로브 | **사람** (기계가 못 만드는 것만) |
| `gen_corpus.py` | **병합 생성기** — canonical source + overlay → 단일 아티팩트 | 스키마 변경 시만 |
| `query_corpus.generated.json` | **생성 산출물** — 모든 소비자가 읽는 단일 코퍼스 | ❌ 손대지 말 것(overlay 고쳐라) |
| `run_corpus.py` | **단일 진입점** — 7 suite HTTP 실행 + 변경감지 | — |
| `README.md` | 본 문서 | — |

**파생 관계(단방향)**:
```
be-3d op_registry.json (96 op, consumerClass A8/B85/C3, runtimeApi) ─┐
gateway router_meta.json (43 라우터 클래스)                          │
be-3d region_camera.ts (34 region), metric_catalog (15 metric)       ├─ gen_corpus.py ─→ query_corpus.generated.json
studio executor_keys.ts (7 executor)                                 │                        │
play100_manifest.ts ∪ scenario_nl_generated.jsonl (B-op NL 커버)     │                        └─ run_corpus.py (모든 서브폴더 HTTP 소비)
query_overlay.jsonc (HAND: probeQuery·fixtures)                     ─┘
```

---

## 2. 모든 서브폴더가 어떻게 쓰나 (공유 사용법)

**서비스 무이동**: 코퍼스는 정의만 공유하고, 실행은 각 repo 가 소유한 서비스(gateway :8030 / studio :3040)를 HTTP 로 호출한다. 어느 폴더에서 돌리든 결과는 같다.

### studio (energy-decision-studio)
```bash
npm run qc:corpus          # 정적 게이트(prebuild 에 이미 배선 — 서비스 불요)
npm run qc:corpus-all      # 전수 라이브 (게이트웨이·studio 필요)
```
`prebuild` 첫 단계에 `run_corpus.py --suite static` 배선됨 → 빌드 전 drift·커버리지 자동 검사.

### gateway / 8.simulation (ems_transformer)
```bash
# 라우터·하드룰 수정 후 라이브 회귀
python ../../projects/energy-contracts/corpus/run_corpus.py --suite capability refuse
```

### be-3d (building-energy-3d)
```bash
# op_registry 재생성(gen_ops.py) 후 — opcode 커버리지·conformance
python ../energy-contracts/corpus/run_corpus.py --changed frontend/src/_shared/op_registry.json
```

### lab / AI 챔피언 (공모전 캠페인)
동일 러너 호출. 캠페인 데모 시나리오(Q-M1~11, e2e_4tracks)는 overlay 의 `queryClasses`·`opProbes` 로 흡수되어 같은 게이트로 검증된다.

---

## 3. 변경 발생 시 — "전수 수행" (사용자 핵심 요구)

`run_corpus.py --changed <파일들>` 이 git diff 파일명을 보고 영향 suite 를 자동 선택:

| 변경 파일 토큰 | 자동 발동 suite |
|---------------|----------------|
| `op_registry.json` | static · opcode · class · scenario |
| `router_meta.json` / `klue_router` | capability · refuse · class |
| `executor_keys` | static · capability |
| `query_overlay` | static · class · opcode · capability · combo |
| `intent.ts` | class · opcode · combo |
| `choropleth` / `f14` / `climate` / `sigungu` | combo |
| `public_scenarios` | scenario |
| `compose` | class · opcode |
| `run24`(=모델 스왑) | **전면**(7 suite 전부) |

```bash
# pre-push 훅 / CI 에서:
python corpus/run_corpus.py --changed $(git diff --name-only origin/master)
```

모델 LoRA 스왑(run##)은 정적 게이트가 못 잡는 회귀(5090-down류)를 포함하므로 **전면 라이브** 발동.

---

## 4. 7 Suite

| suite | 대상 | 서비스 | 판정 |
|-------|------|--------|------|
| **static** | drift 0 + A/C 커버리지 11/11 + B-op 커버리지 리포트 | **불요**(오프라인) | 정적 게이트(CI/prebuild) |
| **class** | queryClasses C/S/L 24 라우팅·컴파일 | gateway + studio | route=cap/compose/ops_status 별 판정 |
| **opcode** | A/C opProbes 11 대표질의 conformance | gateway(+studio) | ops ∈ registry, expectAny 매칭 |
| **capability** | 7 executor 라우팅 hit | gateway | KLUE `/v1/capability-route` |
| **refuse** | off-domain(IAQ/지진/열교/침수/ESS/날씨) 거부 회귀 | gateway | refuse 또는 ops empty = PASS, 오라우팅 = FAIL |
| **combo** | fixtures 차원 조합(region×metric / bldg×sp×climate) **데이터 완전성** | studio + gateway | 200+non-empty, no_data 는 정직 WARN, agg=grid 셀 검증 |
| **scenario** | B-op 3D 시연 재생 표면(public_scenarios 등록 존재) | be-3d(studio 프록시) | `/api/v1/scenarios` 등록 목록 non-empty |

- `--compose` 플래그 지정 시 class/opcode 의 compose 경로도 studio `/api/compose` 로 라이브(느림).
- `--combo-limit N` 으로 combo 케이스 상한(기본 12, 0=전부). combo/scenario 차원은 **fixtures/canonical 에서 파생** — `gen_combo_qc.py` 의 인라인 REGIONS/METRICS 드리프트 문제를 코퍼스가 흡수(전수 pairwise 는 여전히 studio `qc/gen_combo_qc.py` 소관, 여기선 fixtures 대표 조합 스모크).

---

## 5. 코퍼스 갱신 절차

**canonical(op_registry·router_meta·region·executor) 이 바뀐 경우** — 값은 자동 흡수, 재생성만:
```bash
python corpus/gen_corpus.py            # 병합 재생성
python corpus/gen_corpus.py --check    # drift 0 확인 후 커밋
```

**대표 질의/픽스처(사람 판단)를 추가하는 경우** — `query_overlay.jsonc` 만 고친 뒤 재생성:
1. A/C opcode 가 새로 생기면 `opProbes` 에 `probeQuery` 추가 (없으면 static suite 가 **FAIL** 로 미커버 노출).
2. 새 대표 지역/건물은 `fixtures` 에 `why`(선정 이유) 와 함께.
3. `python corpus/gen_corpus.py` → `--check` → 커밋.

**⚠ 정직성·SSOT 규칙(overlay 작성 시 필수)**:
- 픽스처 building PNU 는 **공개 데이터만**. 비공개 실측(GS25/IITP/한수원/NDA)의 PNU·명칭·파일명 금지 → "비공개 한국 실측 데이터셋"으로 익명화(`private-data-disclosure`).
- 절감률·배출계수 등 **canonical 수치 리터럴 금지**. 코퍼스는 질의·기대 op 만 담고, 수치는 라이브 응답에서 검증(`ssot-canonical-compliance`).

---

## 6. 커버리지 현황 (2026-07-30 생성 기준)

```
opcode 96 (A8 / B85 / C3)   router 43   executor 7   metric 15   region 34   queryClass 24
A/C probeQuery : 11/11 커버 (하드 게이트)
B-op           : play100 ∪ scenario_nl 토큰 → 5/85 커버, 80 conformance-only(경고)
```

- **A/C 11종** = studio 직접 책임(최고 회귀 위험) → probeQuery 필수, 없으면 static FAIL.
- **B-op 80종 무NL** = 알려진 conformance-only 전략. compose 가 emit 하면 registry 안에 드는지만 검증(개별 NL 대표질의는 시연 핵심 ~20 우선, 나머지는 비용 대비 효용 낮아 보류). 이 80은 "숨은 미커버"가 아니라 **명시된 커버리지 공백** — WARN 으로 항상 드러난다.

---

*작성: 2026-07-30 | 트리거: 사용자 "완전하게 만들고, AI 챔피언·lab·be-3d 를 비롯한 모든 서브폴더에서 공유" | 설계 정본: energy-decision-studio/docs/QUERY_CORPUS_SSOT.md | 공유 근거: SSOT_GOVERNANCE §9*
