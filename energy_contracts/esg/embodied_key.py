"""구조 + 연대 → embodied factor sub_key 결정.

DB `scope_factors` 테이블의 `(category='embodied', sub_key=...)` lookup 키.

지원 입력 형식 (be-3d / GB 양쪽 통합):
    structure_type: "RC" / "S" / "M" / "W" (영문 대문자)
                  | "철근콘크리트" / "철골" / "조적" / "목조" (한국어)
                  | "steel" / "masonry" / "wood" (영문 소문자, 부분 일치)
    vintage_class: "2010_2017" / "pre1980" / "1980_2000" / "2000_2010" / "post2017" (canonical)
                 | "pre" / "y1980" / "y1990" / "y2000" / "y2010" / "y2017" / "post" (be-3d legacy)

목조 (W) 는 연대 무관 — "W_any" 반환.
"""
from __future__ import annotations


def embodied_key(
    structure_type: str | None,
    vintage_class: str | None,
) -> str:
    """구조 + 연대 → DB sub_key (예: "RC_2010_2017", "S_pre1980", "W_any")."""
    prefix = _normalize_structure(structure_type)

    if prefix == "W":
        return "W_any"

    if prefix not in ("RC", "S", "M"):
        return "_default"

    vintage = _normalize_vintage(vintage_class)
    if vintage is None:
        return "_default"

    return f"{prefix}_{vintage}"


def _normalize_structure(structure_type: str | None) -> str:
    """다양한 표기 → 표준 prefix (RC / S / M / W).

    canonical (GB): RC / S / M / W (대문자, 그대로 prefix)
    Korean (be-3d): 철근콘크리트 → RC / 철골 → S / 조적·벽돌 → M / 목조 → W
    English lowercase: steel → S / masonry → M / wood → W
    """
    if not structure_type:
        return "RC"

    s = structure_type.strip()

    # 영문 대문자 단일자 (canonical)
    if s.upper() in ("RC", "S", "M", "W"):
        return s.upper()

    s_lower = s.lower()
    # 한국어 키워드
    if "철골" in s or "steel" in s_lower:
        return "S"
    if "조적" in s or "벽돌" in s or "masonry" in s_lower:
        return "M"
    if "목" in s or "wood" in s_lower:
        return "W"
    if "철근" in s or "콘크리트" in s or "concrete" in s_lower:
        return "RC"

    return "RC"


def _normalize_vintage(vintage_class: str | None) -> str | None:
    """다양한 표기 → 표준 vintage suffix.

    canonical: 2010_2017 / pre1980 / 1980_2000 / 2000_2010 / post2017
    be-3d legacy: y2010, pre1980, y2000, y2017, post, ...

    None/빈 문자열 → None (호출자가 "_default" 로 fallback) — be-3d 원본 동작 보존.
    """
    if not vintage_class:
        return None

    v = vintage_class.strip()

    # canonical 그대로
    if v in ("pre1980", "1980_2000", "2000_2010", "2010_2017", "post2017"):
        return v

    v_lower = v.lower()
    if "pre" in v_lower and ("1980" in v or v_lower == "pre"):
        return "pre1980"
    if "post" in v_lower or "2017" in v:
        return "post2017"
    if "2010" in v:
        return "2010_2017"
    if "2000" in v:
        return "2000_2010"
    if "1980" in v or "1990" in v:
        return "1980_2000"

    return None
