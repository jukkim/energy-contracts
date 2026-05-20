"""Phase E #5 (E8) — PNU redaction SSOT 단위.

cross-repo `_redact_pnu` 중복 제거 후 wheel 의 단일 구현이 양쪽 호출자
컨벤션과 일치하는지 검증.
"""
from __future__ import annotations

import pytest

from energy_contracts._utils import redact_pnu
from energy_contracts._utils.pnu import redact_pnu as redact_pnu_direct


def test_redact_19digit_pnu():
    """일반 19자리 PNU → 마지막 4자리만."""
    assert redact_pnu("1111010100100010000") == "...0000"
    assert redact_pnu("3611010200100020000") == "...0000"


@pytest.mark.parametrize("inp,expected", [
    ("", "****"),
    ("1", "****"),
    ("12", "****"),
    ("123", "****"),
    ("1234", "****"),  # 정확히 4자리도 전체 마스킹
])
def test_redact_short_inputs_masked(inp, expected):
    assert redact_pnu(inp) == expected


def test_redact_5char_keeps_last_4():
    assert redact_pnu("12345") == "...2345"


def test_package_alias_matches_direct():
    """`_utils.__init__` re-export 가 `_utils.pnu.redact_pnu` 와 동일."""
    assert redact_pnu is redact_pnu_direct
