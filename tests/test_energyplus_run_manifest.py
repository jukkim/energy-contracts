import copy

import jsonschema
import pytest

from energy_contracts import load_schema

SHA = "sha256:" + "a" * 64

def run(setpoint, role):
    return {
        "run_id": f"B02_HC_SP{setpoint}",
        "cooling_setpoint_c": setpoint,
        "role": role,
        "status": "verified",
        "energyplus_version": "24.1.0",
        "input_idf_sha256": SHA,
        "result_sha256": SHA,
        "severe_count": 0,
        "annual_energy_kwh": {
            "electricity": 100000,
            "natural_gas": 20000,
            "district_heating": 0,
            "district_cooling": 0,
            "facility_total": 120000,
        },
        "comfort": {
            "method": "ISO 7730 PMV",
            "warm_limit": 0.7,
            "cold_limit": -0.7,
            "pmv_warmest": 0.5,
            "pmv_coldest": -0.5,
        },
    }

def manifest():
    return {
        "schema_version": "1.0",
        "manifest_id": "eplus-grid-b02-h_c-seoul",
        "created_at": "2026-08-27T00:00:00Z",
        "producer": "mpc-model/sim-campaign",
        "evidence_state": "energyplus_cross_check",
        "building_archetype": {
            "code": "B02",
            "name": "MediumOffice",
            "source_idf_sha256": SHA,
        },
        "hvac_hypothesis": {
            "code": "H_C",
            "label": "Package RTU",
            "is_observed": False,
        },
        "weather": {"city": "Seoul", "epw_sha256": SHA},
        "period": "annual",
        "runs": [
            run(24, "baseline"),
            run(25, "counterfactual"),
            run(26, "counterfactual"),
        ],
    }

def validate(payload):
    jsonschema.Draft202012Validator(load_schema("energyplus_run_manifest")).validate(payload)

def test_valid_triplet():
    payload = manifest()
    validate(payload)
    assert [r["cooling_setpoint_c"] for r in payload["runs"]] == [24, 25, 26]

@pytest.mark.parametrize("mutation", ["severe","observed","wrong_role"])
def test_false_physics_claims_are_rejected(mutation):
    payload = copy.deepcopy(manifest())
    if mutation == "severe":
        payload["runs"][1]["severe_count"] = 1
    elif mutation == "observed":
        payload["hvac_hypothesis"]["is_observed"] = True
    else:
        payload["runs"][0]["role"] = "counterfactual"
    with pytest.raises(jsonschema.ValidationError):
        validate(payload)
