from energy_contracts import load_schema


def test_ecmhs_functions_are_operational():
    functions = {
        item["id"]: item
        for item in load_schema("gateway_routing")["default"]["functions"]
    }

    assert functions["F11a"]["status"] == "operational"
    assert functions["F11b"]["status"] == "operational"
    assert functions["F11c"]["status"] == "operational"
    assert functions["F11b"]["backend"]["upstream_path"] == "/optimize"
    assert functions["F11c"]["backend"]["upstream_path"] == "/compare-strategies"


def test_kbep_forecast_is_bound_to_the_live_endpoint():
    functions = {row["id"]: row for row in load_schema("gateway_routing")["default"]["functions"]}
    assert functions["F9"]["status"] == "operational"
    assert functions["F9"]["path"] == "/v1/kbep/predict"
    assert functions["F9"]["backend"]["upstream_path"] == "/v1/predict"
    assert "fallback" not in functions["F9"]
