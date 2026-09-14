"""구 E-code → M-code 정본 로더와 파생 규칙 (2026-09-15).

## 왜 이 모듈이 있는가

같은 E→M 표가 **두 곳**에 손으로 적혀 있었다 —
`legacy_ems_code_mapping.json#deprecated_e_codes` 와
`ems_strategies.json#default.legacy_mapping.gcs_e_codes`. 둘을 대조하는 검사
(`validate_ssot.check_legacy_code_consistency`)는 있었지만 **없는 경로**
(`legacy["deprecated_e_codes"]`, 실제는 `properties` 아래)를 읽어 빈 dict 와 비교했고,
"정본에 없는 코드는 비교 안 함" 이라 **한 번도 아무것도 비교하지 않았다.** 그 사이
두 표는 E5·E12·E13 유무부터 갈라졌고, 정본 쪽도 E5·E6·E8 을 GCS 생성기 번호 뜻으로
적어 파이프라인이 실제로 내보내는 번호와 달랐다.

그래서:
  * 정본 = `legacy_ems_code_mapping.json` **하나**. 뜻은 `components`(다중 M).
  * `gcs_e_codes` = 이 모듈이 만드는 **투영**(`maps_to`). gen_constants.py --all 이 동기화한다.
  * 읽기 실패·빈 표는 **위반**이다(빈 비교로 초록이 되지 않게).
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "energy_contracts" / "schemas"

#: maps_to 가 가리킬 수 있는 전략 = 시뮬 EMS(M00~M15). DR 제어평면(M16~)은 E-code 의 뜻이 아니다.
SIM_CODES: tuple[str, ...] = tuple(f"M{i:02d}" for i in range(16))


def _load(name: str, schemas_dir: Path | None = None) -> dict:
    return json.loads(((schemas_dir or SCHEMAS_DIR) / name).read_text(encoding="utf-8"))


def canonical_e_codes(schemas_dir: Path | None = None) -> dict[str, dict]:
    """정본 표. 못 읽거나 비어 있으면 ValueError — 호출자는 이것을 위반으로 센다."""
    legacy = _load("legacy_ems_code_mapping.json", schemas_dir)
    try:
        table = legacy["properties"]["deprecated_e_codes"]["properties"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "legacy_ems_code_mapping.json#properties.deprecated_e_codes.properties 를 못 읽었다") from exc
    if not isinstance(table, dict) or not table:
        raise ValueError("legacy_ems_code_mapping.json#deprecated_e_codes 가 비어 있다")
    return table


def atomic_sets(schemas_dir: Path | None = None) -> dict[str, frozenset[str]]:
    """M-code → 그 전략이 켜는 원자 전략 집합(single 은 자기 자신)."""
    strategies = _load("ems_strategies.json", schemas_dir)["default"]["strategies"]
    return {code: frozenset(meta.get("components") or [code]) for code, meta in strategies.items()}


def expected_maps_to(components: list[str], atoms: dict[str, frozenset[str]]) -> tuple[str, bool]:
    """(대표 M-code, exact). 같은 전략이 있으면 그것, 없으면 최소 상위집합, 그것도 없으면 첫 구성요소."""
    want = frozenset(components)
    for code in SIM_CODES:
        if atoms.get(code) == want:
            return code, True
    supersets = sorted((len(atoms[c]), c) for c in SIM_CODES if c in atoms and atoms[c] > want)
    if supersets:
        return supersets[0][1], False
    return components[0], False


def _ecode_order(code: str) -> int:
    return int(code[1:]) if code[1:].isdigit() else 10**6


def gcs_projection(schemas_dir: Path | None = None) -> dict[str, str]:
    """`ems_strategies.json#default.legacy_mapping.gcs_e_codes` 가 가져야 할 값."""
    table = canonical_e_codes(schemas_dir)
    return {code: table[code]["maps_to"] for code in sorted(table, key=_ecode_order)}


def sync_projection(check_only: bool, schemas_dir: Path | None = None) -> bool:
    """gcs_e_codes 를 정본 투영으로 맞춘다. 반환 = 어긋나 있었는가(check_only 면 쓰지 않는다)."""
    path = (schemas_dir or SCHEMAS_DIR) / "ems_strategies.json"
    raw = path.read_text(encoding="utf-8")
    ems = json.loads(raw)
    want = gcs_projection(schemas_dir)
    have = ems.get("default", {}).get("legacy_mapping", {}).get("gcs_e_codes")
    if have == want and list(have) == list(want):
        return False
    if not check_only:
        ems["default"]["legacy_mapping"]["gcs_e_codes"] = want
        path.write_text(json.dumps(ems, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return True


def rule_violations(schemas_dir: Path | None = None) -> list[str]:
    """정본 표 자체의 규칙 위반(구성요소·maps_to·exact) + 투영 불일치."""
    try:
        table = canonical_e_codes(schemas_dir)
        atoms = atomic_sets(schemas_dir)
        enum = set(_load("ems_strategies.json", schemas_dir)["$defs"]["StrategyCode"]["enum"])
    except (OSError, ValueError, KeyError) as exc:
        return [f"legacy E-code 정본 로드 실패 — {exc}"]
    out: list[str] = []
    for code in sorted(table, key=_ecode_order):
        node = table[code]
        comps = node.get("components") if isinstance(node, dict) else None
        if not isinstance(comps, list) or not comps or not all(isinstance(c, str) for c in comps):
            out.append(f"deprecated_e_codes[{code}].components 가 비었거나 문자열 목록이 아니다")
            continue
        unknown = sorted(set(comps) - enum)
        if unknown:
            out.append(f"deprecated_e_codes[{code}].components 에 StrategyCode 밖 코드 {unknown}")
            continue
        want_m, want_exact = expected_maps_to(comps, atoms)
        if node.get("maps_to") != want_m:
            out.append(f"deprecated_e_codes[{code}].maps_to={node.get('maps_to')!r} — 규칙상 {want_m!r} "
                       f"(components={comps}: 같은 전략 → 그것, 없으면 최소 상위집합)")
        if node.get("exact") is not want_exact:
            out.append(f"deprecated_e_codes[{code}].exact={node.get('exact')!r} — 규칙상 {want_exact}")
    try:
        ems = _load("ems_strategies.json", schemas_dir)
        have = ems["default"]["legacy_mapping"]["gcs_e_codes"]
    except (OSError, KeyError) as exc:
        return out + [f"ems_strategies.json#default.legacy_mapping.gcs_e_codes 를 못 읽었다 — {exc}"]
    want = {c: table[c].get("maps_to") for c in table}
    for code in sorted(set(have) | set(want), key=_ecode_order):
        if have.get(code) != want.get(code):
            out.append(f"ems_strategies gcs_e_codes[{code}]={have.get(code)!r} != 정본 maps_to "
                       f"{want.get(code)!r} — gcs_e_codes 는 생성 투영이다: python scripts/gen_constants.py --all")
    return out


def emitter_violations(workspace_root: Path, schemas_dir: Path | None = None,
                       path_for=None) -> tuple[list[str], list[str]]:
    """(위반, 건너뜀 안내). E-code 를 내보내는 파이프라인 선언이 정본에 다 있는가.

    `path_for(rel) -> Path | None` 을 주면 선언 경로를 그 함수로 푼다. None 을 돌려주면
    **커밋 범위 밖**(형제 저장소 소관)이라 건너뛴다 — pre-commit 을 형제 drift 로 막지 않기
    위해서다(2026-09-15). 전수 검사는 path_for 없이 부른다.
    """
    try:
        table = canonical_e_codes(schemas_dir)
        emitters = _load("legacy_ems_code_mapping.json", schemas_dir)[
            "properties"]["drift_guard"]["properties"]["e_code_emitters"]["default"]
    except (OSError, ValueError, KeyError) as exc:
        return [f"E-code emitter 선언 로드 실패 — {exc}"], []
    try:
        import yaml  # type: ignore
    except ImportError:
        return ["E-code emitter 검사에 PyYAML 이 필요하다 (pip install pyyaml)"], []
    out: list[str] = []
    skipped: list[str] = []
    for em in emitters:
        path = path_for(em["path"]) if path_for else workspace_root / em["path"]
        if path is None:
            skipped.append(f"{em['path']} — 커밋 범위 밖(형제 저장소 소관), 여기서 안 봄")
            continue
        if not path.exists():
            skipped.append(f"{em['path']} 없음 — emitter 검사 건너뜀(형제 저장소 미체크아웃)")
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        def dig(dotted: str):
            node = doc
            for part in dotted.split("."):
                node = node.get(part) if isinstance(node, dict) else None
            return node

        labels = dig(em["labels"]) or []
        mapping = dig(em["mapping"]) or {}
        if not labels:
            out.append(f"{em['path']}#{em['labels']} 가 비었다 — emitter 선언을 못 읽었다")
        for code in labels:
            if code not in table:
                out.append(f"{em['path']}#{em['labels']} 의 {code} 가 정본 deprecated_e_codes 에 없다 "
                           f"({em.get('emitter', '')})")
        for code, comps in mapping.items():
            if code not in table:
                out.append(f"{em['path']}#{em['mapping']}[{code}] 가 정본에 없다")
            elif list(comps or []) != list(table[code].get("components") or []):
                out.append(f"{em['path']}#{em['mapping']}[{code}]={list(comps or [])} != 정본 components "
                           f"{table[code].get('components')} — 미러는 손편집 금지, 정본과 맞출 것")
        missing = sorted(set(labels) - set(mapping), key=_ecode_order)
        if missing:
            out.append(f"{em['path']}: {em['labels']} 의 {missing} 에 {em['mapping']} 항목이 없다")
    return out, skipped
