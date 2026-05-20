"""PNU PII redaction — cross-repo SSOT.

Phase E #5 (E8): `_redact_pnu` 가 ems_transformer (`serving/adapters/be3d_client.py`)
와 building-energy-3d (`src/agents/_shared/gateway_client.py`) 에서 동일한
구현으로 중복되어 있었다. 양쪽 사고 시 drift 위험 + monitoring 일관성
저하. 본 모듈을 SSOT 로 통일.

규칙:
  - 19자리 PNU 는 마지막 4자리만 표기 (`...0000`)
  - 4자리 이하 입력은 전체 마스킹 (`****`)
  - 호출자는 logging context 의 prefix (`pnu=`) 를 직접 부여
"""
from __future__ import annotations


def redact_pnu(pnu: str) -> str:
    """PII redaction for PNU (법정 19자리 부동산 코드)."""
    if not pnu or len(pnu) <= 4:
        return "****"
    return f"...{pnu[-4:]}"
