# Bundle Signing Protocol (R13-M3/M4)

## 목적

GB가 생성한 Tech Bundle의 무결성을 Edge가 검증하는 메커니즘.
서명 알고리즘, 공개키 배포, 키 로테이션 절차를 정의한다.

## 서명 알고리즘

- **Ed25519** (RFC 8032)
- 서명 대상: `canonical_json(manifest without signature field)` + `sha256(tar.gz)`
- 인코딩: base64 (standard, padded)

## 공개키 형식

| 항목 | 형식 |
|------|------|
| 키 길이 | 32 bytes (Ed25519 public key) |
| 인코딩 | hex lowercase (64 characters) |
| key_id | `SHA256(pubkey_raw)[:16]` (앞 16자리) |

## 키 저장 (Edge 측)

Edge는 **복수 키 동시 신뢰**를 지원한다 (로테이션 기간 대비).

```
# 방법 1: 환경변수 (colon-separated)
TRUSTED_PUBKEYS=aabb...cc:ddee...ff

# 방법 2: 파일
bundle_store/trusted_keys.json
[
  {"key_id": "abc123...", "pubkey_hex": "aabb...cc", "added_at": "2026-04-21"},
  {"key_id": "def456...", "pubkey_hex": "ddee...ff", "added_at": "2026-03-01"}
]
```

## 검증 흐름 (Edge)

```
1. tar.gz 다운로드
2. manifest.yaml 추출
3. manifest.signature.key_id → trusted_keys에서 검색
4. 미발견 → 번들 거부 (UNTRUSTED_KEY)
5. 발견 → canonical_json(manifest-signature) + sha256(tar) 재계산
6. Ed25519 verify(pubkey, signature, message)
7. 실패 → 번들 거부 (INVALID_SIGNATURE)
8. 성공 → tech별 sha256 검증 → 활성화
```

## 키 로테이션 절차

```
Day 0:  GB 신규 키쌍 생성 (key_id_new)
        Edge에 신키 배포 — trusted_keys에 추가
        (fleet/provision/{ven_id} 또는 수동 env 업데이트)

Day 7:  GB가 신키로 서명 시작
        (구키로 서명된 기존 번들은 여전히 유효)

Day 30: 구키 제거 — trusted_keys에서 삭제
        (구키 서명 번들은 새 sync() 시 거부 → 신키 번들로 교체)
```

## 긴급 폐기 (Key Revocation)

구키 compromise 발견 시:
1. `TRUSTED_PUBKEYS`에서 해당 키 즉시 제거 (fleet/provision 긴급 배포)
2. Edge 재기동 시 해당 키로 서명된 번들 활성화 불가
3. GB가 신키로 재서명된 번들 배포 → Edge auto-sync

## 인증 (Bundle Download)

| 항목 | 값 |
|------|-----|
| 방식 | Bearer Token (정적 공유 시크릿) |
| 헤더 | `Authorization: Bearer {TRUSTED_GB_TOKEN}` |
| Edge 설정 | `TRUSTED_GB_TOKEN` 환경변수 |
| GB 검증 | `hmac.compare_digest(header, GRIDBRIDGE_ADMIN_API_KEY)` |
| 향후 | Phase D에서 mTLS 전환 가능 |

> 선택 근거: 현 규모(수십 대)·내부망 전제에서 (a) 정적 시크릿이 가장 단순.
> JWT(b) / OAuth2(c)는 키 서버 의존성 추가 — 상용화 단계에서 검토.

## 관련 문서

- `schemas/bundle_manifest.json` — signature 필드 정의
- `protocols/commissioning-hash.md` — canonical_json 알고리즘 (동일 함수 사용)
- GridBridge `src/api/catalog.py` — `/bundles/verify` endpoint
- EdgeAgent `src/engineering/bundle_store.py` — `_verify_signature()`
