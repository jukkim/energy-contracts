"""ai_model_registry v1.1 — Track 3 G0 hash freeze 단위 시험 (PRD v1.5).

검증 범위:
1. schema 로딩 + frozen_for_demo / gateway_verify_policy 필드 존재
2. frozen_for_demo 4 모델 모두 models dict 에 존재 (orphan reference 차단)
3. ModelEntry 의 active_checkpoint / backend_url / retrain_type 필드 패턴
4. retrain_type enum 값 ("type_1_sim" | "type_2_real") 유효성
"""
from __future__ import annotations

from energy_contracts import load_schema


def test_schema_loadable() -> None:
    """schema 가 load_schema 로 로딩 가능."""
    r = load_schema("ai_model_registry")
    assert r["version"] == "1.1"
    assert "default" in r
    assert "models" in r["default"]


def test_frozen_for_demo_field_present() -> None:
    """frozen_for_demo (PRD §4.2) 필드 존재 + 비어있지 않음."""
    r = load_schema("ai_model_registry")
    frozen = r["default"].get("frozen_for_demo")
    assert isinstance(frozen, list), "frozen_for_demo must be list"
    assert len(frozen) > 0, "frozen_for_demo cannot be empty"


def test_frozen_models_resolve_to_existing_entries() -> None:
    """frozen_for_demo 각 ID 가 models dict 에 실제 존재 (orphan 차단)."""
    r = load_schema("ai_model_registry")
    frozen = r["default"]["frozen_for_demo"]
    models = r["default"]["models"]
    missing = [mid for mid in frozen if mid not in models]
    assert not missing, f"frozen_for_demo references non-existent models: {missing}"


def test_frozen_models_have_active_checkpoint() -> None:
    """frozen_for_demo 모델은 active_checkpoint 필드 필수 (hash freeze 검증 대상)."""
    r = load_schema("ai_model_registry")
    frozen = r["default"]["frozen_for_demo"]
    models = r["default"]["models"]
    missing = [
        mid for mid in frozen
        if not models[mid].get("active_checkpoint")
    ]
    assert not missing, f"frozen models without active_checkpoint: {missing}"


def test_gateway_verify_policy_valid() -> None:
    """gateway_verify_policy 값이 strict|warn|off 중 하나."""
    r = load_schema("ai_model_registry")
    policy = r["default"].get("gateway_verify_policy", "warn")
    assert policy in ("strict", "warn", "off"), f"invalid policy: {policy}"


def test_retrain_type_enum_values() -> None:
    """retrain_type 필드가 있는 경우 enum 값 유효 (type_1_sim | type_2_real)."""
    r = load_schema("ai_model_registry")
    models = r["default"]["models"]
    valid = {"type_1_sim", "type_2_real"}
    invalid: list[tuple[str, str]] = []
    for mid, m in models.items():
        rt = m.get("retrain_type")
        if rt is not None and rt not in valid:
            invalid.append((mid, rt))
    assert not invalid, f"invalid retrain_type values: {invalid}"


def test_prd_v15_frozen_4_models() -> None:
    """PRD v1.5 §4.2 본선 frozen 4 모델 (korean_bb / ems_transformer / korean_bb_residential / reverse).

    추가 OK, 제거는 금지 — PRD 변경 동반 필요.
    """
    r = load_schema("ai_model_registry")
    frozen = set(r["default"]["frozen_for_demo"])
    required = {"korean_bb", "ems_transformer", "korean_bb_residential", "reverse"}
    missing = required - frozen
    assert not missing, (
        f"PRD v1.5 §4.2 frozen 4 모델 누락: {missing}. "
        "추가 필요 또는 PRD 갱신 동반."
    )


def test_reverse_model_present() -> None:
    """v1.1 신규 — reverse 모델 등재 확인."""
    r = load_schema("ai_model_registry")
    models = r["default"]["models"]
    assert "reverse" in models, "v1.1 신규 reverse 모델 미등재"
    rev = models["reverse"]
    assert rev["framework"] == "lightgbm"
    assert "module_a_macro_f1" in rev["accuracy_metric"]
    assert rev["backend_url"] == "http://localhost:8060"
