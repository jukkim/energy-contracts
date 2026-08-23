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
