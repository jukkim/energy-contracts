"""기능을 operational 로 올린 **근거**를 잠근다.

이전 판은 `status == "operational"` 자체를 단언했다. 그러면 시험이 지키는 것이 근거가
아니라 승격 결정이 된다 — 상류가 완전히 고장 나도 통과하고, 되돌리려 하면 회귀로 보인다.
막던 게이트를 여는 변경에서 확인해야 할 것은 "무엇으로 검증했는가" 다.
"""
import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from energy_contracts import load_schema


def _functions():
    return {item["id"]: item for item in load_schema("gateway_routing")["default"]["functions"]}


def _entry_validator():
    schema = load_schema("gateway_routing")
    return Draft202012Validator(
        {"$ref": "#/$defs/FunctionEntry", "$defs": schema["$defs"]},
        format_checker=FormatChecker(),
    )


def test_promotion_evidence_is_recorded_not_merely_claimed():
    """F9 는 실제 상류 호출로 승격됐고 그 관측값이 계약에 남아 있어야 한다."""
    verified = _functions()["F9"]["verified_by"]
    assert verified["checked_on"], "검증 날짜가 없다"
    assert len(verified["method"]) >= 4, "무엇으로 확인했는지가 없다"
    # "검증함" 같은 주장이 아니라 재현 가능한 관측값이어야 한다.
    assert any(ch.isdigit() for ch in verified["evidence"]), (
        f"근거에 관측값이 없다: {verified['evidence']!r}"
    )


def test_evidence_shape_is_enforced_so_a_bare_claim_cannot_pass():
    """근거 칸이 있어도 형식을 강제하지 않으면 '확인함' 한 마디로 채워진다."""
    validator = _entry_validator()
    sound = json.loads(json.dumps(_functions()["F9"]))
    validator.validate(sound)

    for broken in ({"checked_on": "2026-08-27"},                      # method·evidence 없음
                   {"checked_on": "2026-08-27", "method": "ok",       # 너무 짧다
                    "evidence": "확인"}):
        candidate = json.loads(json.dumps(_functions()["F9"]))
        candidate["verified_by"] = broken
        with pytest.raises(ValidationError):
            validator.validate(candidate)


def test_every_recorded_evidence_block_is_well_formed():
    """근거를 적은 기능은 전부 같은 형식을 지켜야 한다."""
    validator = _entry_validator()
    recorded = [f for f in _functions().values() if "verified_by" in f]
    assert recorded, "근거가 기록된 기능이 하나도 없다"
    for function in recorded:
        validator.validate(json.loads(json.dumps(function)))
