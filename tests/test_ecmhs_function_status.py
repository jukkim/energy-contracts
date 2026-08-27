from energy_contracts import load_schema


def test_ecmhs_prediction_is_operational_without_promoting_optimization():
    functions = {
        item["id"]: item
        for item in load_schema("gateway_routing")["default"]["functions"]
    }

    assert functions["F11a"]["status"] == "operational"
    assert functions["F11b"]["status"] == "operational"
    assert functions["F11c"]["status"] == "operational"
    assert functions["F11b"]["backend"]["upstream_path"] == "/optimize"
    assert functions["F11c"]["backend"]["upstream_path"] == "/compare-strategies"
