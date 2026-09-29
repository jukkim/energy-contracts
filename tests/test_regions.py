"""EC 지역 해석기(regions) — be-3d 시험에서 순수 규칙 시험만 옮김(2026-09-29 T1 ①). be-3d 전용 모듈을 쓰는 시험은 be-3d 에 남는다."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from energy_contracts import regions as rr

def test_table_hash_is_the_file_hash():
    assert rr.table_sha256() == hashlib.sha256(rr.TABLE_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert rr.resolve("부산 중구").table_sha256 == rr.table_sha256()

def test_every_district_round_trips_with_its_province():
    t = rr.table()
    n = bad = 0
    misses = []
    for code, v in t["sigungu"].items():
        if v["same_as_sido"]:
            continue
        n += 1
        q = f"{t['sido'][v['sido']]['name']} {v['name']}"
        r = rr.resolve(q)
        if not (r.ok and r.code == code):
            bad += 1
            misses.append((q, r.status, r.code))
    assert n >= 260 and bad == 0, misses[:10]

def test_every_duplicated_district_name_alone_is_ambiguous():
    """막아야 할 것 — 전국에 둘 이상인 말단 이름(중구·서구·동구·남구·북구·강서구·고성군…)은 시도 없이는 모호."""
    t = rr.table()
    leaves: dict[str, list[str]] = {}
    for code, v in t["sigungu"].items():
        if not v["same_as_sido"]:
            leaves.setdefault(v["name"].split()[-1], []).append(code)
    dup = {k: v for k, v in leaves.items() if len(v) > 1}
    assert {"중구", "서구", "동구", "남구", "북구", "강서구", "고성군"} <= set(dup)
    for leaf, codes in dup.items():
        r = rr.resolve(leaf)
        assert r.status == rr.STATUS_AMBIGUOUS, leaf
        assert {c.code for c in r.candidates} == set(codes), leaf

@pytest.mark.parametrize("q,ctx,code", [
    ("중구", "부산", "26110"), ("중구", "26", "26110"), ("중구", "11", "11140"), ("중구", "2611010100", "26110"),
    ("강서구", "부산광역시", "26440"), ("중구(인천)", None, "28110"), ("부산중구", None, "26110"),
    ("광주시", "경기", "41610"), ("경기 광주시", None, "41610"),
])
def test_context_narrows_same_names(q, ctx, code):
    assert rr.resolve(q, context=ctx).code == code

def test_context_does_not_override_an_explicit_province():
    assert rr.resolve("대구 중구", context="부산").code == "27110"

def test_province_short_name_wins_but_lists_the_district_alternative():
    r = rr.resolve("광주")
    assert r.code == "29" and {c.code for c in r.alternatives} == {"41610"}
    assert rr.resolve("광주시").status == rr.STATUS_AMBIGUOUS     # 광주광역시 ↔ 경기 광주시

def test_retired_province_names_go_to_successor():
    assert rr.resolve("강원도").code == "51" and rr.resolve("전라북도").code == "52"
    assert rr.resolve("부산직할시").code == "26"

def test_numeric_codes_pass_through_even_when_unnamed():
    """숫자는 PNU 접두 — 이름이 없어도 그 코드 그대로(예전 규약). 모르는 이름은 지어내지 않는다."""
    for q in ("43710", "99001", "1168", "1168010100100010000"):
        r = rr.resolve(q)
        assert r.ok and r.code == q
    assert rr.resolve("43710").sigungu_name is None
    assert rr.resolve("42110").sigungu_code == "51110"           # 옛 강원 코드 → 이름·기후는 승계 코드로

_OLD_HAND_ANCHORS = {
    "gangnam_stn": "1168", "samseong_stn": "1168", "yeoksam_stn": "1168", "seolleung_stn": "1168",
    "sinnonhyeon_stn": "1168", "apgujeong_stn": "1168", "garosu_gil": "1168", "sinsa_stn": "1168",
    "seorae_village": "1165", "jamsil_stn": "1171", "lotte_tower": "1171",
    "gwanghwamun": "1111", "jongno_3ga": "1111", "anguk_stn": "1111", "bukchon_hanok": "1111",
    "ikseon_dong": "1111", "namdaemun": "1114", "itaewon": "1117", "seongsan_bridge": "1144",
    "hangang_park": "1156", "yeouido_ifc": "1156",
    "busan_center": "26", "daegu_center": "27", "incheon_center": "28", "gwangju_center": "29",
    "daejeon_center": "30", "ulsan_center": "31",
}

def test_generated_anchor_regions_agree_with_the_old_hand_table():
    """손 표 27건 전부 같은 지역(잠실대교는 제외 — 좌표가 광진구 쪽 교각이라 규칙이 광진을 고른다; 보고서 참조)."""
    got = {aid: rr.resolve(aid).code for aid in _OLD_HAND_ANCHORS}
    assert all(got[a].startswith(p) for a, p in _OLD_HAND_ANCHORS.items()), got
    assert rr.resolve("jamsil_bridge").code == "11215"

def test_all_anchors_resolve():
    anchors = rr.table()["anchors"]
    assert len(anchors) >= 300
    assert [a for a in anchors if not rr.resolve(a).ok] == []

@pytest.mark.parametrize("text,code", [
    ("강남구 사무 건물 보여줘", "11680"), ("부산 중구로 이동해줘", "26110"), ("해운대 보여줘", "26350"),
    ("수원시 장안구 줌", "41111"), ("제주도 가자", "50"),
])
def test_find_region_mention(text, code):
    r = rr.find_region_mention(text)
    assert r is not None and r.ok and r.code == code

def test_find_region_mention_none_and_ambiguous():
    assert rr.find_region_mention("화재 오버레이 켜줘") is None
    assert rr.find_region_mention("중구로 가줘").status == rr.STATUS_AMBIGUOUS

def test_point_disambiguation_picks_the_near_candidate_only():
    r = rr.resolve("중구")
    assert rr.disambiguate_by_point(r, 129.03, 35.10).code == "26110"     # 부산 중구 근처 좌표
    # 두 후보 사이 한가운데면 고르지 않는다
    mid = rr.disambiguate_by_point(rr.resolve("강서구"), (126.85 + 128.95) / 2, (37.55 + 35.2) / 2)
    assert mid.status == rr.STATUS_AMBIGUOUS

@pytest.mark.parametrize("text,code", [
    ("강남구에도 노후 건물이 많아?", "11680"),       # '에도' — 예전엔 '도' 만 떼여 못 풀림
    ("해운대구에도", "26350"),
    ("서울보다 부산이 더워?", "11"),                  # '보다'
    ("습한 도시(창원)와 건조한 도시(대구)", "48120"),  # 괄호도 낱말 경계
])
def test_mentions_resolve_after_josa_and_parentheses(text, code):
    m = rr.find_region_mention(text)
    assert m is not None and m.ok and m.code == code

@pytest.mark.parametrize("text", ["강서구 지도", "중구 EUI", "광주시 에너지"])
def test_ambiguous_names_stay_ambiguous(text):
    m = rr.find_region_mention(text)
    assert m is not None and m.status == rr.STATUS_AMBIGUOUS and len(m.candidates) >= 2

@pytest.mark.parametrize("text", ["수원지 수질", "한국어 질문", "보다 나은 방법"])
def test_non_places_are_not_invented(text):
    assert rr.find_region_mention(text) is None

def test_umbrella_city_carries_children_prefix_only_when_the_table_has_children():
    assert (rr.resolve("수원시").code, rr.resolve("수원시").children_prefix) == ("41110", "4111")
    assert rr.resolve("강남구").children_prefix is None               # 구 하나
    assert rr.resolve("11").children_prefix is None                   # 시도
    assert "children_prefix" in rr.resolve("수원시").to_dict()



# 2026-09-30 Query100 F07 — EC 대상 id 형식(region:<코드>)은 코드와 같은 결과, 숫자가 아니면 이름 있는 거절(양쪽 반례)
def test_target_id_form_resolves_like_the_bare_code():
    schema = json.loads((Path(rr.__file__).parent / "schemas" / "airo_request.json").read_text(encoding="utf-8"))
    pattern = next(r["then"]["properties"]["ids"]["items"]["pattern"] for r in schema["$defs"]["Target"]["allOf"]
                   if r["if"]["properties"]["kind"].get("const") == "region")
    assert pattern.startswith("^" + rr.TARGET_ID_PREFIX)        # 접두는 계약의 것(가정을 시험으로)
    for code in ("11", "4111", "11680"):
        a, b = rr.resolve(rr.TARGET_ID_PREFIX + code), rr.resolve(code)
        assert a.ok and (a.code, a.level, a.label) == (b.code, b.level, b.label)


@pytest.mark.parametrize("bad", ["region:", "region:abc", "region:강남구"])
def test_target_id_form_without_digits_is_a_named_refusal(bad):
    r = rr.resolve(bad)
    assert not r.ok and r.reason == rr.REASON_BAD_CODE


# 2026-09-30 v0.3.66 — 표 지문은 줄끝(CRLF·LF)에 따라 갈리지 않고, 내용이 다르면 갈린다(양쪽 반례)
def test_table_fingerprint_ignores_line_endings_only():
    lf = b'{\n  "a": 1\n}\n'
    crlf = lf.replace(b"\n", b"\r\n")
    assert rr.canonical_table_bytes(crlf) == rr.canonical_table_bytes(lf) == lf
    other = b'{\n  "a": 2\n}\n'
    assert hashlib.sha256(rr.canonical_table_bytes(other)).hexdigest() != hashlib.sha256(rr.canonical_table_bytes(lf)).hexdigest()


def test_gitattributes_pins_data_json_to_lf():
    attrs = (Path(rr.__file__).resolve().parents[1] / ".gitattributes").read_text(encoding="utf-8")
    assert "energy_contracts/data/*.json" in attrs and "eol=lf" in attrs


# 2026-09-30 v0.3.67 — 문장 속 지명: 짧은 지명은 읽고 일상어 어간만 막는다(사용자 결정) · 양쪽 반례
@pytest.mark.parametrize("text", ["예산 10억으로 조합해", "동작 방식을 알려줘", "목표 달성 여부", "음성으로 알려줘",
                                  "심사해 수정해 줘", "10년 동안 사용량"])
def test_everyday_words_are_not_places_in_sentences(text):
    assert rr.find_region_mention(text) is None


@pytest.mark.parametrize("text,code", [("충남 예산 건물", "44810"), ("예산군 건물", "44810"), ("대구 달성군", "27710"),
                                       ("강남 24시간 예측", "11680"), ("마포 노후 건물", "11440"),
                                       ("무안 사랑초", "46840"), ("해운대 날씨", "26350")])
def test_short_place_names_and_marked_stems_are_places(text, code):
    r = rr.find_region_mention(text)
    assert r is not None and r.code == code


def test_field_input_is_not_blocked():
    assert rr.resolve("예산").code == "44810"                          # 사람이 지역 칸에 적은 값은 지명이다


def test_everyday_stem_table_lists_only_real_stems():
    stems = {k for k, v in rr._index().sigungu_by_key.items() if any(g == 1 for _, g in v)}
    assert rr.everyday_stems() and rr.everyday_stems() <= stems        # 표가 낡으면(없는 어간) 빨강
