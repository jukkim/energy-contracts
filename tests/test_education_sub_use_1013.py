"""2026-10-13 Lab 3단계 원형 정직성 — 교육연구시설 = 세부 용도 규칙(building_usage_map v1.4 education_by_sub_use).

반례 양쪽: 학교 세부 용도는 학교 원형으로 가나 · 연구소·학원은 초등학교 원형으로 가지 않나 · 세부 용도 미상은 가정을 밝히나.
"""
from __future__ import annotations

from energy_contracts import axes


def test_primary_school_sub_use_is_primary_school():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10101": 9000.0, "04001": 300.0})
    assert (r["archetype"], r["archetype_basis"], r["flag"], r["absence"]) == ("B07", "sub_use", None, None)
    assert r["sub_use"]["class"] == "primary_school" and r["sub_use"]["share"] == 1.0


def test_high_school_sub_use_is_secondary_school():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10103": 11899.44})
    assert (r["archetype"], r["archetype_basis"]) == ("B08", "sub_use")


def test_research_institute_is_not_primary_school():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10301": 12003.86})
    assert r["archetype"] is None and r["absence"] == "archetype_mismatch"
    assert r["archetype_basis"] == "sub_use" and r["sub_use"]["class"] == "other"


def test_academy_dominant_over_unspecified_is_mismatch():
    # 학원 + 기타교육연구시설(미지정) — 미지정은 빼고 센다
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10003": 4172.8, "10999": 809.48, "03005": 3286.61})
    assert r["archetype"] is None and r["absence"] == "archetype_mismatch"


def test_dominance_by_floor_area():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10101": 5000, "10301": 1000})
    assert r["archetype"] == "B07"
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10101": 1000, "10301": 5000})
    assert r["archetype"] is None


def test_school_level_unknown_is_assumed():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10199": 10156.09})
    assert (r["archetype"], r["archetype_basis"], r["flag"]) == ("B07", "school_level_assumed", "school_level_assumed")


def test_major_class_only_is_explicit_assumption():
    for subs in (None, {}, {"10999": 5517.58}, {"10000": 100.0}, {"14204": 2000.0}):
        r = axes.usage_to_archetype("교육연구시설", sub_uses=subs)
        assert (r["archetype"], r["archetype_basis"], r["flag"]) == ("B07", "major_class_assumed", "major_class_assumed"), subs
    # 별칭(학교)도 같은 행 → 같은 규칙
    assert axes.usage_to_archetype("학교")["archetype_basis"] == "major_class_assumed"


def test_other_rows_unchanged():
    # 세부 용도 규칙이 없는 행은 sub_uses 를 무시하고 예전 결과 그대로(archetype_basis 칸 없음)
    r = axes.usage_to_archetype("의료시설", sub_uses={"10301": 100})
    assert r == {"archetype": "B12", "flag": None, "absence": None, "basis": r["basis"]}
    assert axes.usage_to_archetype("업무시설", 30000, sub_uses={"10101": 1})["archetype"] == "B01"


def test_mismatch_absence_declared():
    absence = axes.usage_archetype_table()["absence"]
    assert absence["archetype_mismatch"]["absence_kind"] == "missing"


# ── v1.5 name_fallback(2026-10-14) — 세부 용도를 모를 때만 대장 건물명으로 학교 급 ──

def test_name_middle_school_without_sub_use_is_secondary():
    r = axes.usage_to_archetype("교육연구시설", sub_uses={}, building_name="중동중학교")
    assert (r["archetype"], r["archetype_basis"], r["flag"]) == ("B08", "register_name", "school_level_from_name")


def test_name_high_school_and_primary_school():
    assert axes.usage_to_archetype("교육연구시설", building_name="서울중동고등학교")["archetype"] == "B08"
    assert axes.usage_to_archetype("교육연구시설", building_name="대치초등학교")["archetype"] == "B07"
    assert axes.usage_to_archetype("교육연구시설", building_name="대치초등학교")["archetype_basis"] == "register_name"


def test_name_does_not_override_known_sub_use():
    # 층별 세부 용도가 연구소면 이름에 '고등학교'가 있어도 결손 그대로(이름은 모를 때만)
    r = axes.usage_to_archetype("교육연구시설", sub_uses={"10301": 5000.0}, building_name="과학고등학교 연구동")
    assert r["archetype"] is None and r["absence"] == "archetype_mismatch"


def test_name_ambiguous_or_not_school_keeps_major_class_assumption():
    for nm in ("OO초중학교 통합", "한국기술연구원", "", None):
        r = axes.usage_to_archetype("교육연구시설", sub_uses={}, building_name=nm)
        assert (r["archetype"], r["archetype_basis"], r["flag"]) == ("B07", "major_class_assumed", "major_class_assumed"), nm


def test_name_source_parcel_titles_has_its_own_basis_v1_6():
    """v1.6(GPT R121 §5): 확정 필지 표제부 이름에서 온 학교 급은 근거가 따로('같은 필지 건물명으로 추정') · 자신의 표제부 이름은 그대로 register_name.
    반례: 모르는 원천은 조용히 register_name 이 되지 않고 멈춘다 · 원천을 밝혀도 두 갈래 이름이면 대분류 가정."""
    parcel = axes.usage_to_archetype("교육연구시설", None, building_name={"name": "중동중학교 / 중동고등학교", "source": "parcel_titles"})
    assert parcel["archetype"] == "B08" and parcel["archetype_basis"] == "parcel_register_names" and parcel["building_name_source"] == "parcel_titles"
    own = axes.usage_to_archetype("교육연구시설", None, building_name="중동중학교")
    assert own["archetype_basis"] == "register_name" and own["building_name_source"] == "register_title"
    assert axes.usage_to_archetype("교육연구시설", None, building_name={"name": "중동중학교", "source": "register_title"})["archetype_basis"] == "register_name"
    import pytest
    with pytest.raises(ValueError):
        axes.usage_to_archetype("교육연구시설", None, building_name={"name": "중동중학교", "source": "guess"})
    mixed = axes.usage_to_archetype("교육연구시설", None, building_name={"name": "대모초등학교 / 대왕중학교", "source": "parcel_titles"})
    assert mixed["archetype_basis"] == "major_class_assumed"
    labels = axes.usage_archetype_table()["education_by_sub_use"]["archetype_basis_labels"]
    assert labels["parcel_register_names"] == "같은 필지 건물명으로 추정"
