# -*- coding: utf-8 -*-
"""지역 해석기 하나 — EC 정본(2026-09-29 T1 ① · v0.3.64 초안). 원본 = be-3d `src/visualization/region_resolver.py`
(규칙·표 그대로 옮김 — be-3d·게이트웨이가 이 모듈을 import 해 지명 해석을 한 곳으로: 설계 = 캠페인
`docs/QUERY100_NEXT_BATCH_DESIGN_2026-09-29.md` 'T1 설계'). 표 = `data/region_resolver_table.json`(be-3d 생성기
`scripts/gen_region_resolver_table.py` 출력 — 생성기를 EC 로 옮기는 것은 T1 ④).

원래 설명:
지역 해석기 하나 — 이름·코드·앵커 id·PNU → {시도, 시군구, 동, 대표점, 기후 도시} (2026-09-28).

be-3d 의 모든 지역 해석(지표 지도·선택·커버리지·음성·F14 대상 문맥)은 이 모듈을 부른다.
규칙은 여기 한 곳, 표는 `data/region_resolver_table.json` 한 벌(scripts/gen_region_resolver_table.py 생성).
행정구역 이름을 이 파일에 적지 않는다 — 전부 표에서 읽는다.

모르는 것은 채우지 않는다:
  · 동명 시군구(중구 6곳·서구·강서구·고성군 …)는 상위 문맥(시도)이 글 안에 있거나 `context` 로 오면 그것으로
    좁히고, 없으면 `status="ambiguous"` + 후보 목록(되묻기용)을 돌려준다. 서울로 두지 않는다.
  · 해석 못 한 글은 `status="unresolved"` 와 이유 이름. 기본 지역(강남·서울)을 넣지 않는다.
  · 시도 줄임말(광주)이 시군구 줄임(경기 광주시)과 겹치면 시도가 이기고, 겹친 쪽은 `alternatives` 로 싣는다.
  · 리(里) — 법정동 코드 끝 두 자리가 00 이 아닌 마을 — 이름은 상위 문맥(시군구·읍면)이 글 안에 없으면 단독으로
    잡지 않는다(`region_village_needs_context`). '거리'·'우리'처럼 흔한 낱말이 마을 이름이라 '이태원 거리'의
    '거리'가 울주군 상북면 거리리로 잡혔다(2026-09-28). 문장 속 지역 찾기는 앵커 이름(이태원 거리)을 먼저 본다.

반환 `code` = PNU 접두 의미의 지역 코드(전국 "" · 시도 2 · 시군구 5 · 동 10 · 필지 19). 숫자 입력은 그대로
돌려준다(옛 코드로 적재된 필지 범위를 바꾸지 않는다) — 이름·기후 도시는 승계 코드로 읽는다.
하위 구를 거느린 시(수원시 41110)는 5자리 그대로이고, 필지 범위는 `pnu_range_prefix` 가 4자리로 넓힌다.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

TABLE_PATH = Path(__file__).resolve().parent / "data" / "region_resolver_table.json"
#: 가상 필지 접두 — be-3d `src.shared.parcel_code.VIRTUAL_PARCEL_PREFIX` 와 같은 값. be-3d 가 이 모듈을 import 하는 단계(T1 ②)에서
#:   be-3d 쪽이 이 상수를 읽게 바꿔 한 곳으로 합친다(그 전까지 두 값이 같은지 시험이 본다).
VIRTUAL_PARCEL_PREFIX = "99"
TABLE_SCHEMA = "region-resolver-table-v1"

#: 전국을 뜻하는 말. 빈 글도 전국이다(지표 지도의 옛 규약).
NATION_WORDS = frozenset({"전국", "대한민국", "한국", "국내", "nation", "kr", "KR"})
#: 지역 이름 뒤에 붙어도 뜻이 바뀌지 않는 말 — 떼고 해석한다.
IGNORABLE_WORDS = frozenset({"일대", "전체", "전역", "지역", "권역", "관내", "내", "안"})

STATUS_RESOLVED = "resolved"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_UNRESOLVED = "unresolved"

REASON_EMPTY_NOT_NATION = "region_empty"
REASON_NO_MATCH = "region_name_not_found"
REASON_AMBIGUOUS = "region_ambiguous"
REASON_BAD_CODE = "region_code_not_found"
REASON_TRAILING = "region_trailing_words_not_found"
REASON_VILLAGE_NEEDS_CONTEXT = "region_village_needs_context"
#: EC error_response 1.1 Refusal.code — 지명 모호의 이름은 하나(2026-09-29 검토 A3: 게이트웨이와 같은 `PLACE_AMBIGUOUS`).
#:   옛 이름(`region_ambiguous`·장면 입구의 `REGION_AMBIGUOUS`)은 `legacy_code` 로만 남는다.
PLACE_AMBIGUOUS_CODE = "PLACE_AMBIGUOUS"


def is_village_code(code: str) -> bool:
    """리(里) 수준 법정동 코드 — 10자리이고 끝 두 자리가 00 이 아니다(읍·면·동은 00)."""
    return len(code) == 10 and code.isdigit() and code[8:] != "00"


@dataclass(frozen=True)
class Candidate:
    code: str
    level: str
    label: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RegionResolution:
    status: str
    query: str
    code: Optional[str] = None
    level: Optional[str] = None            # nation | sido | sigungu | dong | parcel | building
    label: Optional[str] = None            # 사람이 읽는 이름(동명이면 시도 줄임을 붙인다: '부산 중구')
    sido_code: Optional[str] = None
    sido_name: Optional[str] = None
    sigungu_code: Optional[str] = None     # 승계(현행) 코드
    sigungu_name: Optional[str] = None
    dong_code: Optional[str] = None
    dong_name: Optional[str] = None
    point: Optional[dict[str, Any]] = None  # {lon, lat, source}
    climate_city: Optional[str] = None     # KBEP 18도시 축(climate_common 과 같은 이름). 모르면 None
    climate_city_source: Optional[str] = None
    via: Optional[str] = None              # nation | code | anchor | name | dong | pnu
    candidates: tuple[Candidate, ...] = ()
    alternatives: tuple[Candidate, ...] = ()
    reason: Optional[str] = None
    table_sha256: str = field(default="")
    #: 우산 시(구를 둔 시 — 수원 41110 → 권선구 41113 …)의 하위 접두 4자리. 대상 전개는 이것을 읽는다(2026-09-29 M4 결정 ①:
    #:   게이트웨이는 4자리 접두, be-3d 는 5자리 시 코드를 냈다 — 둘 다 싣는다). 우산 시가 아니면 None.
    children_prefix: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == STATUS_RESOLVED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["candidates"] = [c.to_dict() for c in self.candidates]
        d["alternatives"] = [c.to_dict() for c in self.alternatives]
        return d


class RegionResolutionError(ValueError):
    """모호·미해석 — 이름 있는 거절. `.resolution` 에 후보가 있다."""

    def __init__(self, resolution: RegionResolution):
        self.resolution = resolution
        names = ", ".join(c.label for c in resolution.candidates[:8])
        msg = f"{resolution.reason}: {resolution.query!r}" + (f" — 후보: {names}" if names else "")
        super().__init__(msg)

    def detail(self) -> dict[str, Any]:
        r = self.resolution
        refusal = ({"code": PLACE_AMBIGUOUS_CODE, "legacy_code": r.reason, "kind": "question", "retry": "ask"}
                   if r.status == STATUS_AMBIGUOUS else {})
        return {"error": r.reason, "status": r.status, "query": r.query, **refusal,
                "candidates": [c.to_dict() for c in r.candidates],
                "message": ("지역이 여러 곳입니다 — 시도를 함께 말씀해 주세요" if r.status == STATUS_AMBIGUOUS
                            else "지역을 찾지 못했습니다 — 시도·시군구·동 이름이나 코드로 말씀해 주세요")}


# ── 표 ─────────────────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _raw_bytes() -> bytes:
    return TABLE_PATH.read_bytes()


@lru_cache(maxsize=1)
def table() -> dict[str, Any]:
    doc = json.loads(_raw_bytes().decode("utf-8"))
    if doc.get("schema") != TABLE_SCHEMA:
        raise RuntimeError(f"지역 해석 표 형식이 다르다: {doc.get('schema')!r} ≠ {TABLE_SCHEMA}")
    return doc


def canonical_table_bytes(raw: bytes) -> bytes:
    """지문용 표 바이트 — 줄끝을 LF 로 맞춘다(2026-09-30 v0.3.66). 같은 표가 git 체크아웃(core.autocrlf)에 따라 CRLF 로
    풀려 체크아웃마다 다른 지문이 됐다(메인 01c72d7d… ↔ wheel a86590aa…). 줄끝 말고는 바꾸지 않는다(내용이 다르면 다른 지문)."""
    return raw.replace(b"\r\n", b"\n")


def table_sha256() -> str:
    """표 지문 — 두 소비처가 같은 표를 읽는지 대조하는 값(줄끝 정규화 바이트의 해시 · ``canonical_table_bytes``)."""
    return hashlib.sha256(canonical_table_bytes(_raw_bytes())).hexdigest()


def _leaf(name: str) -> str:
    return name.split()[-1]


def _stem(leaf: str) -> Optional[str]:
    """시·군·구 접미를 뗀 줄임(강남구 → 강남). 한 글자만 남으면 줄이지 않는다(중구 → X)."""
    if leaf[-1:] in ("시", "군", "구") and len(leaf) >= 3:
        return leaf[:-1]
    return None


@dataclass
class _Index:
    sido_by_name: dict[str, tuple[str, int]]          # 이름 → (코드, 등급) 등급 0 = 정식·옛 정식 이름, 1 = 줄임
    sigungu_by_key: dict[str, list[tuple[str, int]]]  # 이름 → [(코드, 등급)] 0 = 정식·말단 이름, 1 = 줄임
    dong_by_tail: dict[str, list[str]]                 # 시군구 뒤 전체 이름 → [동 코드]
    dong_by_leaf: dict[str, list[str]]                 # 말단 이름 → [동 코드]
    leaf_count: dict[str, int]                         # 시군구 말단 이름 → 전국 개수(라벨 모호 판정)


@lru_cache(maxsize=1)
def _index() -> _Index:
    t = table()
    sido_by_name: dict[str, tuple[str, int]] = {}
    for c, v in t["sido"].items():
        sido_by_name[v["name"]] = (c, 0)
        sido_by_name.setdefault(v["short"], (c, 1))
    for n, c in t["sido_retired_names"].items():
        sido_by_name.setdefault(n, (c, 0))
    sgg: dict[str, list[tuple[str, int]]] = {}

    def add(key: str, code: str, grade: int) -> None:
        lst = sgg.setdefault(key, [])
        if all(x != code for x, _ in lst):
            lst.append((code, grade))

    leaf_count: dict[str, int] = {}
    for c, v in t["sigungu"].items():
        if v["same_as_sido"]:
            continue   # 세종: 시군구 이름이 시도 이름 — 시도로 해석한다
        name = v["name"]
        add(name, c, 0)
        add(name.replace(" ", ""), c, 0)
        leaf = _leaf(name)
        add(leaf, c, 0)
        leaf_count[leaf] = leaf_count.get(leaf, 0) + 1
        st = _stem(leaf)
        if st:
            add(st, c, 1)
    # 특별시·광역시의 'X시' 부름(서울시·광주시) — 시군구 정식 이름과 같은 등급이라 겹치면 모호가 된다.
    for c, v in t["sido"].items():
        if v["name"].endswith(("특별시", "광역시", "특별자치시")):
            sido_by_name.setdefault(v["short"] + "시", (c, 0))
    dong_by_tail: dict[str, list[str]] = {}
    dong_by_leaf: dict[str, list[str]] = {}
    for c, tail in t["dong"].items():
        dong_by_tail.setdefault(tail, []).append(c)
        dong_by_leaf.setdefault(_leaf(tail), []).append(c)
    return _Index(sido_by_name, sgg, dong_by_tail, dong_by_leaf, leaf_count)


# ── 이름·라벨 ──────────────────────────────────────────────────────────────────────────────

def canonical_sigungu(code: str) -> str:
    """옛·폐지 시군구 코드 → 현행(승계) 코드. 모르면 그대로."""
    t = table()
    succ = t["sigungu_successor"].get(code)
    if succ:
        return succ
    new_sido = t["sido_successor"].get(code[:2])
    if new_sido and (new_sido + code[2:]) in t["sigungu"]:
        return new_sido + code[2:]
    return code


#: 표에 이름이 없어도 범위 조회를 허락하는 코드 자릿수 — 시군구 5 · 읍면동 8(법정동 앞 8) · 법정동 10 · 필지 19 · 건물 25.
_UNNAMED_CODE_LENGTHS = frozenset({5, 8, 10, 19, 25})


def _unnamed_code_shape_ok(code: str) -> bool:
    """표에 없는 숫자 코드를 범위 조회용으로 받아도 되는가 — 자릿수가 행정 코드 층이고, 앞 2자리가 표의 시도
    (옛 코드 승계 포함) 또는 가상 필지 접두(parcel_code.VIRTUAL_PARCEL_PREFIX)일 때만. 청원군 43710 같은 분할 폐지
    코드·가상 필지 99…·표 밖 법정동은 받고, "1"·"0000"·"123" 은 받지 않는다."""
    if not code.isdigit() or len(code) not in _UNNAMED_CODE_LENGTHS:
        return False
    return code[:2] == VIRTUAL_PARCEL_PREFIX or canonical_sido(code[:2]) in table()["sido"]


def canonical_sido(code: str) -> str:
    return table()["sido_successor"].get(code, code)


def sido_name(code: str) -> Optional[str]:
    v = table()["sido"].get(canonical_sido(code))
    return v["name"] if v else None


def sido_codes(*, include_name_only: bool = False) -> list[str]:
    return sorted(c for c, v in table()["sido"].items() if include_name_only or v["status"] == "live")


def sido_name_to_code() -> dict[str, str]:
    """정식 시도 이름 → 코드(현행 + 이름만 있는 통합 코드). 옛 이름·줄임은 `resolve` 가 받는다."""
    return {v["name"]: c for c, v in table()["sido"].items()}


def umbrella_codes() -> frozenset[str]:
    """하위 구를 거느린 시 코드(표에서 파생). 필지 범위는 4자리로 넓혀야 한다."""
    return frozenset(c for c, v in table()["sigungu"].items() if v["umbrella"])


def pnu_range_prefix(code: str) -> str:
    """지역 코드 → 필지(PNU) 범위 접두. 우산 시(현행·옛 코드 모두)는 4자리."""
    if len(code) == 5 and code.isdigit() and canonical_sigungu(code) in umbrella_codes():
        return code[:4]
    return code


def sigungu_label(code: str) -> Optional[str]:
    """시군구 이름 — 말단 이름이 전국에 하나면 그대로(강남구), 여럿이면 시도 줄임을 붙인다(부산 중구)."""
    t = table()
    c = canonical_sigungu(code)
    v = t["sigungu"].get(c)
    if v is None:
        return None
    if v["same_as_sido"]:
        return v["name"]
    leaf = _leaf(v["name"])
    if _index().leaf_count.get(leaf, 0) > 1:
        return f"{t['sido'][v['sido']]['short']} {v['name']}"
    return v["name"]


def region_label(code: str) -> str:
    """지역 코드(전국·시도·시군구·우산 4자리·동·필지) → 사람이 읽는 이름. 모르면 코드 그대로(정직)."""
    if not code:
        return "전국"
    r = resolve(code)
    return r.label if r.ok and r.label else code


# ── 해석 ──────────────────────────────────────────────────────────────────────────────────

def _cand(code: str, level: str) -> Candidate:
    t = table()
    if level == "sido":
        return Candidate(code, level, t["sido"][code]["name"])
    if level == "sigungu":
        v = t["sigungu"][code]
        full = v["name"] if v["same_as_sido"] else f"{t['sido'][v['sido']]['name']} {v['name']}"
        return Candidate(code, level, full)
    sg = code[:5]
    return Candidate(code, level, f"{_cand(sg, 'sigungu').label} {t['dong'][code]}")


def _point(lonlat: Optional[list], source: str) -> Optional[dict[str, Any]]:
    return {"lon": lonlat[0], "lat": lonlat[1], "source": source} if lonlat else None


def _from_code(query: str, code: str, via: str, *, point: Optional[dict] = None,
               level: Optional[str] = None) -> RegionResolution:
    """숫자 코드 → 해석. code 는 PNU 접두 의미로 그대로 돌려준다."""
    t = table()
    sha = table_sha256()
    if code == "":
        return RegionResolution(STATUS_RESOLVED, query, code="", level="nation", label="전국", via=via,
                                point=point, table_sha256=sha)
    n = len(code)
    sido_c = canonical_sido(code[:2])
    sd = t["sido"].get(sido_c)
    if sd is None:
        return RegionResolution(STATUS_UNRESOLVED, query, reason=REASON_BAD_CODE, table_sha256=sha)
    if n == 2:
        return RegionResolution(STATUS_RESOLVED, query, code=code, level=level or "sido", label=sd["name"],
                                sido_code=sido_c, sido_name=sd["name"],
                                point=point or _point(sd.get("rep"), "sido_building_weighted"),
                                climate_city=sd.get("climate_city"),
                                climate_city_source="sido_single_station" if sd.get("climate_city") else None,
                                via=via, table_sha256=sha)
    if n == 4:
        # 우산 시의 4자리 접두(수원 4111) — 그 접두의 우산 시가 하나면 그 시로 읽는다.
        #   우산 시가 아니면 그 접두를 가진 현행 시군구가 하나일 때만(옛 앵커 표의 1168 = 강남구).
        ums = [c for c in umbrella_codes() if c[:4] == canonical_sigungu(code + "0")[:4]]
        if not ums:
            ums = [c for c in t["sigungu"] if c[:4] == code]
        if len(ums) != 1:
            return RegionResolution(STATUS_UNRESOLVED, query, reason=REASON_BAD_CODE, table_sha256=sha)
        r = _from_code(query, ums[0], via, point=point)
        return RegionResolution(**{**asdict(r), "code": code, "candidates": (), "alternatives": ()})
    sgg_c = canonical_sigungu(code[:5])
    sv = t["sigungu"].get(sgg_c)
    if sv is None:
        return RegionResolution(STATUS_UNRESOLVED, query, reason=REASON_BAD_CODE, table_sha256=sha)
    base = dict(sido_code=sv["sido"], sido_name=t["sido"][sv["sido"]]["name"], sigungu_code=sgg_c,
                sigungu_name=sv["name"], climate_city=sv.get("climate_city"),
                climate_city_source="sigungu_nearest_station" if sv.get("climate_city") else None,
                via=via, table_sha256=sha)
    sg_label = sigungu_label(sgg_c)
    if n == 5:
        return RegionResolution(STATUS_RESOLVED, query, code=code, level=level or "sigungu", label=sg_label,
                                point=point or _point(sv.get("rep"), "sigungu_building_weighted"), **base)
    dong_c = sgg_c + code[5:10] if n >= 10 else None
    dong_nm = t["dong"].get(dong_c) if dong_c else None
    if n == 10:
        if dong_nm is None:
            return RegionResolution(STATUS_UNRESOLVED, query, reason=REASON_BAD_CODE, table_sha256=sha)
        return RegionResolution(STATUS_RESOLVED, query, code=code, level=level or "dong",
                                label=f"{sg_label} {dong_nm}", dong_code=dong_c, dong_name=dong_nm,
                                point=point or _point(sv.get("rep"), "sigungu_building_weighted"), **base)
    lvl = level or ("parcel" if n == 19 else "building" if n == 25 else "prefix")
    return RegionResolution(STATUS_RESOLVED, query, code=code, level=lvl,
                            label=f"{sg_label} {dong_nm}" if dong_nm else sg_label,
                            dong_code=dong_c if dong_nm else None, dong_name=dong_nm,
                            point=point or _point(sv.get("rep"), "sigungu_building_weighted"), **base)


def _anchor(query: str, aid: str) -> RegionResolution:
    a = table()["anchors"][aid]
    pt = {"lon": a["lon"], "lat": a["lat"], "source": "anchor"} if a.get("lon") is not None else None
    if a.get("code") is None:
        return RegionResolution(STATUS_UNRESOLVED, query, reason=REASON_NO_MATCH, table_sha256=table_sha256())
    return _from_code(query, a["code"], "anchor", point=pt, level=a.get("level"))


def _context_sido(context: Optional[str]) -> Optional[str]:
    """문맥(시도 이름·줄임·코드·하위 지역 코드) → 시도 코드. 모르면 None."""
    if not context:
        return None
    c = context.strip()
    if c.isdigit() and len(c) >= 2:
        return canonical_sido(canonical_sigungu(c[:5])[:2] if len(c) >= 5 else c[:2])
    hit = _index().sido_by_name.get(c)
    if hit:
        return hit[0]
    r = resolve(c)
    return r.sido_code if r.ok else None


_PAREN = re.compile(r"^(.+?)\s*\(([^)]+)\)\s*$")


def _tokens(query: str) -> tuple[list[str], Optional[str]]:
    q = re.sub(r"\s+", " ", query.strip())
    ctx = None
    m = _PAREN.match(q)
    if m:                       # '중구(부산)' — 괄호는 상위 문맥
        q, ctx = m.group(1).strip(), m.group(2).strip()
    toks = [x for x in q.split(" ") if x]
    while toks and toks[-1] in IGNORABLE_WORDS:
        toks.pop()
    return toks, ctx


def _split_glued_sido(tok: str) -> Optional[list[str]]:
    """'부산중구' 처럼 붙여 쓴 시도 — 가장 긴 시도 이름 접두로 나눈다."""
    for name in sorted(_index().sido_by_name, key=len, reverse=True):
        if tok.startswith(name) and len(tok) > len(name):
            return [name, tok[len(name):]]
    return None


def resolve(query: Optional[str], *, context: Optional[str] = None) -> RegionResolution:
    """지역 해석. `context` = 대화·대상 문맥의 시도(이름·코드) — 글 안에 시도가 없을 때만 동명을 좁힌다."""
    r = _resolve(query, context=context, sido_head=True)
    if r.status == STATUS_UNRESOLVED and r.via is None:
        # 앞머리가 시도 줄임(광주)으로 읽혔지만 뒤가 그 시도에 없으면 — 시군구 줄임(경기 광주시)으로 다시 읽는다.
        r2 = _resolve(query, context=context, sido_head=False)
        if r2.status != STATUS_UNRESOLVED:
            r = r2
    return _with_children_prefix(r)


def _with_children_prefix(r: RegionResolution) -> RegionResolution:
    """우산 시면 하위 접두 4자리를 싣는다 — 표의 다른 시군구가 같은 4자리로 시작할 때만(짐작하지 않는다)."""
    from dataclasses import replace
    code = r.code or ""
    if not (r.ok and len(code) == 5 and code.endswith("0")):
        return r
    head = code[:4]
    if any(c != code and c.startswith(head) for c in table()["sigungu"]):
        return replace(r, children_prefix=head)
    return r


#: EC 대상 id 의 지역 접두 — ``airo_request.json`` ``$defs.Target`` 의 region ids pattern(``^region:[0-9]{2}([0-9]{2,3})?$``).
#: 표면·게이트웨이 장면 조리법은 지역을 이 형식으로 싣는다(2026-09-30 Query100 F07: be-3d 선택이 ``region:11680`` 을 지명으로
#: 읽어 0동 — 처리기마다 접두를 벗기던 사본 둘이 이미 있었다). 해석기 입구 한 곳에서 떼고 숫자 경로(코드 모양 판정)로 보낸다.
TARGET_ID_PREFIX = "region:"


def _resolve(query: Optional[str], *, context: Optional[str], sido_head: bool) -> RegionResolution:
    sha = table_sha256()
    q = (query or "").strip()
    if q.startswith(TARGET_ID_PREFIX):
        code = q[len(TARGET_ID_PREFIX):].strip()
        if not code.isdigit():                                   # 'region:' · 'region:abc' — 이름 있는 거절(지명으로 읽지 않는다)
            return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_BAD_CODE, table_sha256=sha)
        q = code
    if not q or q in NATION_WORDS:
        return _from_code(q, "", "nation")
    if q.isdigit():
        r = _from_code(q, q, "code")
        if r.ok:
            return r
        if not _unnamed_code_shape_ok(q):
            # 2026-09-28 화이트박스 C2: 표에 없는 숫자를 모두 resolved 로 내 "1"(=서울 범위)·"0000"(0건)이 빈 성공이 됐다.
            #   이름 없는 코드는 행정 코드 모양일 때만 받는다(아래 함수) — 아니면 이름 있는 거절.
            return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_BAD_CODE, table_sha256=sha)
        # 숫자는 PNU 접두다 — 표에 이름이 없어도(청원군 43710 같은 분할 폐지 코드, 가상 필지 99…) 범위 조회는
        #   그 코드 그대로 한다(예전 규약 유지). 이름·기후 도시는 모른다고 싣는다(지어내지 않는다).
        lvl = {2: "sido", 4: "prefix", 5: "sigungu", 10: "dong", 19: "parcel", 25: "building"}.get(len(q), "prefix")
        split = table()["sigungu_split"].get(q[:5]) if len(q) >= 5 else None
        return RegionResolution(STATUS_RESOLVED, q, code=q, level=lvl, via="code_unnamed",
                                reason="region_code_not_in_table",
                                candidates=tuple(_cand(c, "sigungu") for c in (split or [])
                                                 if c in table()["sigungu"]),
                                table_sha256=sha)
    t = table()
    if q in t["anchors"]:
        return _anchor(q, q)
    toks, paren_ctx = _tokens(q)
    if not toks:
        return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_EMPTY_NOT_NATION, table_sha256=sha)
    idx = _index()

    # 1) 앞머리 시도
    sido_c: Optional[str] = None
    sido_grade: Optional[int] = None
    if toks[0] not in idx.sido_by_name and len(toks) == 1 and toks[0] not in idx.sigungu_by_key \
            and toks[0] not in idx.dong_by_leaf:
        glued = _split_glued_sido(toks[0])
        if glued:
            toks = glued
    if toks[0] in idx.sido_by_name and (sido_head or len(toks) == 1 or idx.sido_by_name[toks[0]][1] == 0):
        sido_c, sido_grade = idx.sido_by_name[toks[0]]
        rest = toks[1:]
    else:
        rest = toks
    explicit_sido = sido_c
    ctx_sido = explicit_sido or _context_sido(paren_ctx) or _context_sido(context)

    def within(codes: list[str]) -> list[str]:
        if ctx_sido is None:
            return codes
        inside = [c for c in codes if c[:2] == ctx_sido]
        # 글 안의 시도는 강제, 대화 문맥은 좁힐 수 있을 때만 좁힌다(사용자가 지역을 바꿨을 수 있다).
        return inside if (inside or explicit_sido) else codes

    if not rest:
        # 시도 하나 — 단, 'X시' 부름(광주시)이 시군구 정식 이름(경기 광주시)과 겹치면 같은 등급이라 모호다.
        r = _from_code(q, sido_c, "name")
        same = [c for c, g in idx.sigungu_by_key.get(toks[0], []) if g == 0]
        official = toks[0] in {v["name"] for v in t["sido"].values()} or toks[0] in t["sido_retired_names"]
        if same and sido_grade == 0 and not official:
            other = _context_sido(paren_ctx) or _context_sido(context)
            if other == sido_c:
                return r
            inside = [c for c in same if other and c[:2] == other]
            if len(inside) == 1:
                return _from_code(q, inside[0], "name")
            cands = (_cand(sido_c, "sido"),) + tuple(_cand(c, "sigungu") for c in same)
            return RegionResolution(STATUS_AMBIGUOUS, q, candidates=cands, reason=REASON_AMBIGUOUS,
                                    table_sha256=sha)
        alts = tuple(_cand(c, "sigungu") for c, _ in idx.sigungu_by_key.get(toks[0], []))
        return RegionResolution(**{**asdict(r), "alternatives": alts, "candidates": ()}) if alts else r

    # 2) 시군구 — 가장 긴 앞머리부터. 등급 0(정식·말단 이름)이 있으면 등급 1(줄임)은 버린다.
    sgg_hits: list[str] = []
    used = 0
    for k in range(len(rest), 0, -1):
        key = " ".join(rest[:k])
        hits = idx.sigungu_by_key.get(key) or idx.sigungu_by_key.get(key.replace(" ", "")) or []
        if hits:
            best = min(g for _, g in hits)
            cands = within([c for c, g in hits if g == best])
            if cands:
                sgg_hits, used = cands, k
                break
    rest2 = rest[used:]
    # 우산 시 다음의 하위 구(수원 장안구)
    if sgg_hits and rest2:
        kids = [c for c, g in idx.sigungu_by_key.get(rest2[0], [])
                if t["sigungu"][c]["parent"] in sgg_hits]
        if kids:
            sgg_hits, rest2 = kids, rest2[1:]

    # 3) 동
    if rest2 or not sgg_hits:
        dong_part = rest2 if sgg_hits else rest
        if not dong_part:
            return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_NO_MATCH, table_sha256=sha)
        if not sgg_hits and not sido_head and sido_c is None and len(rest) > 1:
            # 재시도(앞머리를 시군구 줄임으로 읽기)인데 시군구가 안 잡혔다 — 앞 낱말을 버리고 동만 읽지 않는다.
            return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_NO_MATCH, table_sha256=sha)
        tail = " ".join(dong_part)
        # 전체 이름(가곡면 가대리)이 맞거나, 한 낱말이면 말단 이름. 여러 낱말 중 끝만 보고 앞을 버리지 않는다.
        by_tail = idx.dong_by_tail.get(tail)
        pool = by_tail or (idx.dong_by_leaf.get(dong_part[0], []) if len(dong_part) == 1 else [])
        # 리(마을)는 상위 문맥이 있을 때만 — 시군구가 잡혔거나, 전체 이름에 읍·면이 들어 있을 때(가곡면 가대리).
        village_context = bool(sgg_hits) or (by_tail is not None and len(dong_part) > 1)
        if not village_context:
            villages = [c for c in pool if is_village_code(c)]
            pool = [c for c in pool if not is_village_code(c)]
            if villages and not pool:
                return RegionResolution(STATUS_UNRESOLVED, q, reason=REASON_VILLAGE_NEEDS_CONTEXT,
                                        candidates=tuple(_cand(c, "dong") for c in sorted(villages)[:20]),
                                        table_sha256=sha)
        if sgg_hits:
            heads = set(sgg_hits) | {k for k in t["sigungu"] if t["sigungu"][k]["parent"] in sgg_hits}
            pool = [c for c in pool if c[:5] in heads]
        pool = within(pool)
        if not pool:
            reason = REASON_TRAILING if sgg_hits else REASON_NO_MATCH
            return RegionResolution(STATUS_UNRESOLVED, q, reason=reason,
                                    candidates=tuple(_cand(c, "sigungu") for c in sgg_hits), table_sha256=sha)
        if len(pool) > 1:
            return RegionResolution(STATUS_AMBIGUOUS, q, reason=REASON_AMBIGUOUS,
                                    candidates=tuple(_cand(c, "dong") for c in sorted(pool)), table_sha256=sha)
        return _from_code(q, pool[0], "dong")

    if len(sgg_hits) > 1:
        return RegionResolution(STATUS_AMBIGUOUS, q, reason=REASON_AMBIGUOUS,
                                candidates=tuple(_cand(c, "sigungu") for c in sorted(sgg_hits)), table_sha256=sha)
    return _from_code(q, sgg_hits[0], "name")


def _km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def disambiguate_by_point(res: RegionResolution, lon: float, lat: float,
                          *, min_ratio: float = 2.0) -> RegionResolution:
    """모호 결과 + 좌표(카메라·앵커) → 대표점이 가장 가까운 후보. 둘째 후보가 min_ratio 배 이상 멀 때만 고른다.

    좌표가 문맥을 대신하는 자리(지도 슬러그 카메라 중심)에서만 쓴다 — 말로 한 질문에는 되묻기가 맞다.
    """
    if res.status != STATUS_AMBIGUOUS or not res.candidates:
        return res
    t = table()
    dist = []
    for c in res.candidates:
        rep = (t["sigungu"].get(c.code) or t["sido"].get(c.code) or {}).get("rep") if c.level != "dong"             else (t["sigungu"].get(c.code[:5]) or {}).get("rep")
        if rep:
            dist.append((_km(lon, lat, rep[0], rep[1]), c))
    dist.sort(key=lambda x: x[0])
    if not dist or (len(dist) > 1 and dist[1][0] < min_ratio * max(dist[0][0], 1.0)):
        return res
    r = _from_code(res.query, dist[0][1].code, "name")
    return RegionResolution(**{**asdict(r), "via": "name+point"})


#: 지역 이름 뒤에 붙는 조사 — 문장에서 지역을 찾을 때만 뗀다(긴 것부터).
#: 긴 것부터(첫 일치 하나만 뗀다). 2026-09-29 M4: '에도·에게·보다·처럼·에서도' 추가 — '강남구에도' 가 '도' 만 떼여 못 풀렸다
#:   (게이트웨이 목록과의 합집합 — 조사 떼기 사본 5벌 통합의 첫 걸음).
_JOSA = ("에서는", "에서도", "에서", "으로", "까지", "부터", "에는", "에도", "에게", "보다", "처럼",
         "로", "에", "의", "은", "는", "이", "가", "을", "를", "도", "만")


_ANCHOR_PAREN = re.compile(r"\s*\([^)]*\)\s*")


@lru_cache(maxsize=1)
def _anchor_names() -> tuple[tuple[str, str], ...]:
    """(띄어쓰기 없앤 앵커 이름, 앵커 id) — 긴 이름부터. 지역 중심 앵커(region_*·광역 중심)는 이름이 곧 지역
    이름이라 뺀다(지역은 이름 해석이 맡는다). 괄호 설명('(3호선)')은 뗀다. 두 글자 이하는 흔한 낱말과 겹쳐 뺀다."""
    out = []
    for aid, a in table()["anchors"].items():
        if a.get("code") is None or a.get("level") in ("nation", "sido") or aid.startswith("region_"):
            continue
        name = _ANCHOR_PAREN.sub(" ", a.get("name") or "").replace(" ", "")
        if len(name) > 2:
            out.append((name, aid))
    return tuple(sorted(out, key=lambda x: (-len(x[0]), x[1])))


def find_region_mention(text: str, *, context: Optional[str] = None,
                        max_words: int = 3) -> Optional[RegionResolution]:
    """문장 속 지역 언급 → 해석(해석됨 또는 모호). 앵커 이름(이태원 거리·강남역 사거리)을 먼저, 그다음 가장 긴
    낱말 묶음부터 본다. 없으면 None.

    음성·자유 문장처럼 지역 칸이 따로 없는 입력용. 모호하면 모호 결과를 그대로 돌려준다(되묻기).
    """
    flat = re.sub(r"\s+", "", text or "")
    # 앵커가 여럿이면(공덕역에서 국회의사당까지) 먼저 나온 것, 같은 자리면 긴 이름.
    hits = [(flat.find(name), -len(name), name, aid) for name, aid in _anchor_names() if name in flat]
    if hits:
        _, _, name, aid = min(hits)
        return RegionResolution(**{**asdict(_anchor(name, aid)), "query": name})
    # 괄호도 낱말 경계다 — '습한 도시(창원)와' 의 '창원'(2026-09-29 M4: 게이트웨이만 읽던 모양)
    words = [w for w in re.split(r"[\s,.!?·()\[\]]+", text or "") if w]
    for n in range(min(max_words, len(words)), 0, -1):
        for i in range(0, len(words) - n + 1):
            chunk = words[i:i + n]
            tries = [chunk]
            for j in _JOSA:
                if chunk[-1].endswith(j) and len(chunk[-1]) > len(j) + 1:
                    tries.append(chunk[:-1] + [chunk[-1][: -len(j)]])
                    break
            for c in tries:
                q = " ".join(c)
                if q in NATION_WORDS or q.isdigit() or q in table()["anchors"]:
                    continue
                r = resolve(q, context=context)
                if r.status != STATUS_UNRESOLVED:
                    return r
    return None


def resolve_code(query: Optional[str], *, context: Optional[str] = None) -> str:
    """해석된 지역 코드(PNU 접두 의미). 모호·미해석은 RegionResolutionError(이름 있는 거절)."""
    r = resolve(query, context=context)
    if not r.ok:
        raise RegionResolutionError(r)
    return r.code or ""
