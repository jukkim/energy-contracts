"""H_E 행 하나(2026-09-28 사용자 결정) — E·HE 두 행이 8칸에서 판정이 갈려 소비처마다 다른 답을 냈다.
HE 가 정본 행, E 는 row_aliases 로 HE 를 가리킨다. 양쪽 반례: E 행을 다시 넣으면 거절 · HE 행은 통과."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from energy_contracts._pydantic_models.hvac_ems_matrix import Matrix

SCHEMA = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas" / "hvac_ems_matrix.json"
REGION = SCHEMA.parent / "region_codes.json"


def _doc():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_one_row_for_h_e_and_alias_points_to_it():
    d = _doc()["default"]
    assert "E" not in d["matrix"] and "HE" in d["matrix"]
    assert d["row_aliases"] == {"E": "HE"}
    assert all(target in d["matrix"] for target in d["row_aliases"].values())


def test_alias_agrees_with_region_codes():
    """별칭은 region_codes 의 같은 설비(H_E: sim_id=HE, aliases E·HE)와 맞는다 — economizer·staging 없음."""
    he = json.loads(REGION.read_text(encoding="utf-8"))["default"]["hvac_types"]["H_E"]
    assert he["sim_id"] == "HE" and "E" in he["aliases"]
    assert he["economizer_m02"] is False and he["staging_m03"] is False
    row = _doc()["default"]["matrix"]["HE"]
    assert row["M02"]["compatibility"] in ("infeasible", "expected_skip")        # economizer 없음
    assert row["M03"]["compatibility"] in ("infeasible", "expected_skip")        # staging 없음


def test_schema_rejects_a_second_h_e_row_but_accepts_the_canonical_one():
    m = _doc()["default"]["matrix"]
    Matrix.model_validate(m)                                                     # 반례: 정본 행은 통과
    with pytest.raises(ValidationError):
        Matrix.model_validate({**m, "E": m["HE"]})                              # E 행을 다시 넣으면 거절
