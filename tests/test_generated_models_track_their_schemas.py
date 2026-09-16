"""생성된 pydantic 모델이 스키마를 따라왔는가.

`energyplus_run_manifest.json` 이 v1.1 에서 존 증거를, v1.3 에서 `period_hours` 를 얻는
동안 `_pydantic_models/energyplus_run_manifest.py` 는 **두 세대 모두 놓쳤다**. 두 PR 다
스키마와 CHANGELOG 만 고쳤고, 재생성을 부르는 단계가 체인 어디에도 없었기 때문이다.
생성본은 조용히 낡는다 — 스키마를 읽는 쪽은 맞고 모델을 import 하는 쪽은 틀린 채로.

이 시험은 재생성하지 않는다(codegen 은 느리고 헤더가 매번 달라 diff 가 난다). 대신
스키마가 선언한 **모든 속성 이름이 생성본에 나타나는지**만 본다. 필드 하나가 통째로
빠지는 이 사고의 모양을 정확히 잡고, 타입이 바뀌는 경우는 잡지 못한다 — 후자는
`validate_ssot.py` 가 스키마 자체를 본다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "energy_contracts"
SCHEMAS = sorted((ROOT / "schemas").glob("*.json"))
MODELS = ROOT / "_pydantic_models"


def _property_names(node) -> set[str]:
    """스키마가 선언한 속성 이름 전부, `$defs` 안쪽까지."""
    names: set[str] = set()
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            names |= set(properties)
        for value in node.values():
            names |= _property_names(value)
    elif isinstance(node, list):
        for value in node:
            names |= _property_names(value)
    return names


def _model_path(schema: Path) -> Path:
    return MODELS / (schema.stem + ".py")


@pytest.mark.parametrize("schema", SCHEMAS, ids=lambda p: p.stem)
def test_every_schema_property_appears_in_its_generated_model(schema):
    model = _model_path(schema)
    if not model.is_file():
        pytest.skip(f"[해당 없음] {schema.stem} 에는 생성 모델이 없다 — 통과가 아니다")
    declared = _property_names(json.loads(schema.read_text(encoding="utf-8")))
    source = model.read_text(encoding="utf-8")
    # `_usage`/`_consumers` 같은 메타 키는 모델에 실리지 않는다.
    missing = sorted(name for name in declared
                     if not name.startswith("_") and name not in source)
    assert missing == [], (
        f"{model.name} 이 스키마보다 낡았다. 빠진 속성: {missing}. "
        f"`python scripts/gen_pydantic_models.py --all` 로 재생성하고, 그 스키마의 "
        f"모델만 커밋한다(나머지는 헤더의 임시 파일명만 바뀐다)."
    )
