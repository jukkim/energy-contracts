import copy
import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from energy_contracts import list_schemas, load_schema


ROOT = Path(__file__).resolve().parents[1]


def _example() -> dict:
    return json.loads(
        (ROOT / "examples" / "building_model_packet.json").read_text(encoding="utf-8")
    )


def _validate(payload: dict) -> None:
    Draft202012Validator(
        load_schema("building_model_packet"), format_checker=FormatChecker()
    ).validate(payload)


def test_building_model_packet_example_is_valid_and_has_no_energy_values() -> None:
    payload = _example()
    _validate(payload)

    assert set(payload["assignments"]) == {"baseline", "scenario", "profile"}
    assert payload["serving_receipt"]["replay"]["replay_hash"].startswith("sha256:")

    def keys(node):
        found = set()
        if isinstance(node, dict):
            found.update(node)
            for child in node.values():
                found.update(keys(child))
        elif isinstance(node, list):
            for child in node:
                found.update(keys(child))
        return found

    forbidden_numeric_results = {
        "energy_kwh",
        "energy_kwh_m2",
        "annual_energy_kwh",
        "savings_kwh",
        "savings_pct",
        "prediction",
        "forecast",
    }
    assert keys(payload).isdisjoint(forbidden_numeric_results)


def test_building_model_packet_schema_is_valid_and_carries_no_result_values() -> None:
    schema = load_schema("building_model_packet")
    Draft202012Validator.check_schema(schema)

    def property_names(node):
        found = set()
        if isinstance(node, dict):
            found.update((node.get("properties") or {}).keys())
            for child in node.values():
                found.update(property_names(child))
        elif isinstance(node, list):
            for child in node:
                found.update(property_names(child))
        return found

    assert property_names(schema).isdisjoint(
        {
            "energy_kwh",
            "energy_kwh_m2",
            "annual_energy_kwh",
            "savings_kwh",
            "savings_pct",
            "prediction",
            "forecast",
        }
    )


def test_schema_is_discoverable_and_catalogued() -> None:
    assert "building_model_packet" in list_schemas()
    index = (ROOT / "energy_contracts" / "schemas" / "_index.yaml").read_text(
        encoding="utf-8"
    )
    assert "BuildingModelPacket:" in index
    assert "building_model_packet.json" in index


@pytest.mark.parametrize(
    ("mutation", "path"),
    [
        ("unsupported_as_active", ("assignments", "profile")),
        ("hard_ood_as_active", ("assignments", "scenario")),
        ("surrogate_without_lineage", ("assignments", "scenario")),
        ("served_without_output_hash", ("serving_receipt",)),
        ("forecast_without_issued_at", ("assignments", "profile", "weather", "snapshot")),
    ],
)
def test_unsafe_or_unreplayable_packet_is_rejected(mutation: str, path: tuple) -> None:
    payload = copy.deepcopy(_example())
    node = payload
    for part in path:
        node = node[part]

    if mutation == "unsupported_as_active":
        node["model_class"] = "U"
        node["grade"] = "U"
    elif mutation == "hard_ood_as_active":
        node["ood"]["hard_ood"] = True
        node["ood"]["status"] = "out_of_domain"
    elif mutation == "surrogate_without_lineage":
        node.pop("eplus_lineage")
    elif mutation == "served_without_output_hash":
        node.pop("output_hash")
    else:
        node.pop("issued_at")

    with pytest.raises(jsonschema.ValidationError):
        _validate(payload)


def test_u_assignment_can_record_an_explicit_refusal_without_fabricated_model() -> None:
    payload = _example()
    unsupported = payload["assignments"]["profile"]
    unsupported.update(
        {
            "status": "unsupported",
            "model_class": "U",
            "grade": "U",
            "reason_codes": ["MISSING_AREA"],
            "ood": {
                **unsupported["ood"],
                "status": "out_of_domain",
                "hard_ood": True,
                "reason_codes": ["MISSING_AREA"],
            },
        }
    )
    unsupported.pop("model_version_ref")
    unsupported.pop("eplus_lineage")
    unsupported.pop("model_artifacts")
    unsupported["weather"].pop("snapshot")
    payload["overall_grade"] = "U"
    payload["serving_receipt"] = None

    _validate(payload)
