# Commissioning Hash 알고리즘 (SSOT)

> 작성 2026-04-20 (ARCH-R8-1 AUDIT-R2). 소유 Edge 팀. 리뷰 VW/GB.

Edge 기사 설치 세션 `seal` 시 생성되는 `commissioning_hash` 의 결정론적 알고리즘.
`schemas/engineering_session.json#/properties/commissioning_hash` 에서 참조.

이 문서가 **유일한 사양 (Single Source of Truth)**. Edge·GB·VW 3계층이 동일 입력에
대해 반드시 동일 해시를 산출해야 `fleet/engineering/{ven_id}` retain 의 재검증,
감사, 타임라인 일관성이 성립한다.

## 입력

```json
{
  "selected_techs": [<sort 된 tech id 배열>],
  "provisioning_config": <provision.json#/config 전체 객체>,
  "bundle_version": "<semver 문자열, 예: 1.3.0>",
  "technician_id": "<문자열. 값 없으면 빈 문자열 \"\">"
}
```

키 4개는 **고정**. 순서 무관(아래 canonical 정규화가 정렬함).

## 정규화 (canonical JSON)

```python
import json, hashlib

payload = {
    "selected_techs": sorted(selected_techs),
    "provisioning_config": provisioning_config,
    "bundle_version": bundle_version,
    "technician_id": technician_id or "",
}
canon = json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
digest = "sha256:" + hashlib.sha256(canon).hexdigest()
```

### 불변 조건 (MUST)

1. `sort_keys=True` — 중첩된 모든 객체 포함.
2. `separators=(",", ":")` — 공백 금지.
3. `ensure_ascii=False` — 한글·UTF-8 그대로 유지 (Edge/GB 모두 동일 바이트를
   얻기 위함). `ensure_ascii=True` 를 쓰면 `\uXXXX` 이스케이프로 바이트 길이가
   달라져 해시가 어긋난다.
4. 인코딩 `UTF-8` (BOM 없음).
5. `selected_techs` 를 해시 진입 *전에* 반드시 `sorted()` 처리. 중복 제거는 안 함
   (현재 스키마가 `uniqueItems: true` 로 사전 차단).
6. `technician_id` 가 `None` / 누락이면 빈 문자열로 정규화.
7. 접두 `sha256:` 고정.

## 구현 위치

| 계층 | 모듈 | 비고 |
|------|------|------|
| Edge | `src/engineering/session_store.py::compute_commissioning_hash` | seal 시점 생성 + 로컬 파일 저장 |
| GB   | 재검증 시 `engineering_session.json` 수신 후 재계산 → 비교 | 구현 대기 |
| VW   | 감사·타임라인 렌더 시 재계산 가능 (선택) | 구현 대기 |

공유 유틸은 각 프로젝트 내부 `utils/canonical_json` 로 수렴. 중복 구현 금지.

## 테스트 벡터 (호환성 고정)

입력 A (ASCII):
```json
{"selected_techs":["pre-cooling","ess-discharge"],
 "provisioning_config":{"ven_id":"VEN-STORE-001","kind":"telemetry","backend":"replay"},
 "bundle_version":"1.3.0",
 "technician_id":"tech_kim"}
```

예상:
- `selected_techs` 정렬 후 → `["ess-discharge","pre-cooling"]`
- canon(요약) = `{"bundle_version":"1.3.0","provisioning_config":{"backend":"replay","kind":"telemetry","ven_id":"VEN-STORE-001"},"selected_techs":["ess-discharge","pre-cooling"],"technician_id":"tech_kim"}`
- digest = `sha256:` + SHA-256(UTF-8 바이트)

입력 B (한글 포함):
```json
{"selected_techs":[],
 "provisioning_config":{"ven_id":"VEN-STORE-001","notes":"점포 A — 옥상 실외기"},
 "bundle_version":"1.3.0",
 "technician_id":""}
```

한글이 `\uXXXX` 로 이스케이프되지 않아야 (`ensure_ascii=False` 검증 포인트).

## 변경 관리

- 필드 추가: 기존 해시가 깨지므로 **major bump** 필요 (`v2` 로 프로토콜 분기).
  v1 에서 수신자가 신규 필드를 무시하더라도 해시는 맞춰줘야 하므로, 현재는
  `selected_techs / provisioning_config / bundle_version / technician_id` 4개로
  **고정**. 새 필드가 생기면 이 문서를 먼저 개정한다.
- 필드 제거: **금지**. 하위 호환 깨짐.

## 관련

- `schemas/engineering_session.json` — 세션 스키마
- `schemas/engineering_diff.json` — 세션 간 차이 기록
- Edge `docs/DESIGN-EDGE-ENGINEERING.md` §4 — seal 플로우
