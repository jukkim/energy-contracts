import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from energy_contracts import load_schema


ROOT = Path(__file__).resolve().parents[1]


def _validate(schema_name: str, example_name: str) -> dict:
    payload = json.loads((ROOT / "examples" / example_name).read_text(encoding="utf-8"))
    Draft202012Validator(
        load_schema(schema_name), format_checker=FormatChecker()
    ).validate(payload)
    return payload


def test_building_passport_example_is_valid() -> None:
    passport = _validate("building_passport", "building_passport.json")
    assert passport["data_tier"] == "building_and_measured"
    assert passport["availability"]["realtime_telemetry"] is False


def test_flexibility_envelope_example_is_valid_and_sign_safe() -> None:
    envelope = _validate("flexibility_envelope", "flexibility_envelope.json")
    interval = envelope["intervals"][0]
    assert interval["downward_flex_kw"] >= 0
    assert interval["rebound_energy_kwh"] >= 0
    assert envelope["persistent_efficiency_ref"]


def test_flexibility_and_annual_efficiency_are_separate_axes() -> None:
    schema = load_schema("flexibility_envelope")
    props = schema["properties"]
    assert "annual_savings_kwh" not in props
    assert "persistent_efficiency_ref" in props


def test_model_binding_example_is_valid_and_never_grants_physics_verdict() -> None:
    binding = _validate("model_binding", "model_binding.json")
    assert "physics_verdict" in binding["prohibited_uses"]
    assert "physics_verdict" not in binding["allowed_uses"]


def test_field_evidence_event_example_is_valid_and_append_only_shaped() -> None:
    event = _validate("field_evidence_event", "field_evidence_event.json")
    assert event["event_type"] == "recommendation"
    assert event["previous_event_hash"] is None
    assert event["event_hash"].startswith("sha256:")


def test_question_spec_example_is_valid_and_cannot_carry_capability_fields() -> None:
    """A parser may report intent and stated conditions; never data tier or control."""
    spec = _validate("question_spec", "question_spec.json")
    assert spec["intent"] == "setpoint"
    assert spec["provenance"]["evidence_state"] == "llm_interpreted"

    schema = load_schema("question_spec")
    forbidden = set(schema["$defs"]["ForbiddenCapabilityFields"]["default"])

    def keys(node):
        found = set()
        for name, child in (node.get("properties") or {}).items():
            found.add(name)
            if isinstance(child, dict):
                found |= keys(child)
        return found

    assert keys(schema).isdisjoint(forbidden)


# ── v1.1 (2026-09-25): 계열에 따라 필수 칸이 갈린다 — 막을 것과 통과시킬 것 양쪽 ─────

def _binding(**over) -> dict:
    base = json.loads((ROOT / "examples" / "model_binding.json").read_text(encoding="utf-8"))
    base.update(over)
    return {k: v for k, v in base.items() if v is not None}


def _errors(payload: dict) -> list:
    return list(Draft202012Validator(load_schema("model_binding"), format_checker=FormatChecker())
                .iter_errors(payload))


def test_an_ml_surrogate_without_its_feature_hash_is_refused():
    assert _errors(_binding(model_family="surrogate_ml", feature_schema_hash=None))


def test_a_physics_model_with_not_applicable_passes_without_ml_hashes():
    ok = _binding(model_family="physics_site", model_id="eplus_site_model",
                  feature_schema_hash=None, checkpoint_hash=None, feature_schema_status="not_applicable")
    assert not _errors(ok)


def test_a_physics_model_must_say_the_feature_schema_does_not_apply():
    """반례: 물리 모델이 표시 없이 오면 막는다 — 칸이 빠진 것과 '해당 없음' 은 다르다."""
    silent = _binding(model_family="physics_archetype", feature_schema_hash=None, checkpoint_hash=None)
    assert _errors(silent)
    wrong = _binding(model_family="grid_table", feature_schema_hash=None, feature_schema_status="hashed")
    assert _errors(wrong)


def test_the_family_is_required():
    assert _errors(_binding(model_family=None))
