"""순수 규칙 함수 — 정본 원문 한 벌 (2026-09-28 일반화 G1).

이 파일의 ``BEGIN PURE RULES`` 아래 본문은 ``scripts/gen_constants.py`` 가 **그대로** 각 소비 저장소의
``_generated_constants.py`` 에 싣는다(바이트 동일 — EC ``tests/test_generalization_g1.py`` 가 대조). 그래서 규칙이
두 곳에 따로 적히지 않는다(용도→원형 8벌·백분위수 2방식·별칭 대조 5벌이 갈렸던 자리).

제약(생성본에 실리므로):
  * import 금지 — 표준 내장만 쓴다.
  * 표는 인자로 받거나, 인자가 없으면 모듈 전역(생성본의 USAGE_ARCHETYPE·AXIS_ALIAS_INDEX)에서 찾는다.
    그 전역이 없는 생성본에서 부르면 LookupError(이름 있는 실패) — 빈 표로 조용히 통과하지 않는다.
"""
from __future__ import annotations

# --- BEGIN PURE RULES ---


def ec_axis_key(token: object) -> str:
    """축 별칭 대조 열쇠 — 공백·밑줄·하이픈·가운뎃점·탭을 빼고 casefold."""
    return "".join(ch for ch in str(token) if ch not in " _-·\t").casefold()


def ec_axis_tables(doe_buildings: dict, simulation_cities: dict, hvac_types: dict, strategies: dict,
                   kbep_fast_path: list) -> dict:
    """축 어휘 네 표 → {strategies, index, kbep}. 별칭 하나가 두 코드를 가리키면 ValueError(조용히 고르지 않는다).

    index[kind][ec_axis_key(토큰)] = 정본 코드. 토큰 = 코드·KBEP 정수·영문·snake·한글·별칭.
    kbep[kind][코드] = KBEP 정수(전략은 fast-path 안만)."""
    fast = set(kbep_fast_path or [])
    strat = {code: {"name_en": m.get("name_en"), "name_kr": m.get("name_kr"),
                    "kbep_id": int(code[1:]) if code in fast else None}
             for code, m in strategies.items()}
    index: dict = {"archetype": {}, "city": {}, "hvac": {}, "strategy": {}}

    def put(kind: str, tok: object, code: str) -> None:
        if tok is None or tok == "":
            return
        k = ec_axis_key(tok)
        if index[kind].get(k, code) != code:
            raise ValueError(f"축 별칭 충돌: {kind} {tok!r} → {index[kind][k]} 와 {code}")
        index[kind][k] = code

    for code, m in doe_buildings.items():
        for tok in [code, m.get("kbep_id"), m.get("name_en"), m.get("snake"), m.get("name_kr"), *(m.get("aliases") or [])]:
            put("archetype", tok, code)
    for code, m in simulation_cities.items():
        for tok in [code, m.get("kbep_city_id"), m.get("name_en"), m.get("name_kr"), *(m.get("aliases") or [])]:
            put("city", tok, code)
    for code, m in hvac_types.items():
        for tok in [code, m.get("kbep_id"), m.get("sim_id"), *(m.get("aliases") or [])]:
            put("hvac", tok, code)
    for code, m in strat.items():
        for tok in [code, int(code[1:]), m.get("name_en")]:
            put("strategy", tok, code)
    kbep = {"archetype": {c: m["kbep_id"] for c, m in doe_buildings.items() if m.get("kbep_id") is not None},
            "city": {c: m["kbep_city_id"] for c, m in simulation_cities.items() if m.get("kbep_city_id") is not None},
            "hvac": {c: m["kbep_id"] for c, m in hvac_types.items() if m.get("kbep_id") is not None},
            "strategy": {c: m["kbep_id"] for c, m in strat.items() if m["kbep_id"] is not None}}
    return {"strategies": strat, "index": {k: dict(sorted(v.items())) for k, v in index.items()}, "kbep": kbep}


def ec_axis_encode(kind: str, token: object, index: dict | None = None) -> str:
    """축 토큰(코드·영문·한글·snake·KBEP 정수·별칭) → 정본 코드(Bxx·Cxx·H_x·Mxx).

    모르는 토큰은 KeyError('AXIS_TOKEN_UNKNOWN …') — 기본값으로 채우지 않는다(모르는 도시를 서울로 두던 자리)."""
    idx = index if index is not None else globals().get("AXIS_ALIAS_INDEX")
    if idx is None:
        raise LookupError("AXIS_ALIAS_INDEX 가 이 생성본에 없다 — gen_constants exports 에 넣는다")
    table = idx.get(kind)
    if table is None:
        raise KeyError(f"AXIS_KIND_UNKNOWN: {kind!r} (있는 것: {sorted(idx)})")
    code = table.get(ec_axis_key(token)) if token is not None else None
    if code is None:
        raise KeyError(f"AXIS_TOKEN_UNKNOWN: {kind} {token!r}")
    return code


def ec_usage_to_archetype(usage: object, gross_floor_area_m2: object = None, table: dict | None = None,
                          floors_above: object = None) -> dict:
    """건축물대장 주용도·자산 용도(+연면적·지상 층수) → 원형. 결과 = {archetype, flag, absence, basis}.

    * 업무시설 = 연면적 구간(결정 D1). 연면적이 없거나 0 이하이면 면적 미상 원형 + flag='area_unverified'.
    * 공동주택 = 지상 층수 구간(apartment_by_floors, 2026-09-28 X2). 층수 미상이면 unknown_floors 원형(기존 값).
      층수로 **용도**를 바꾸지 않는다(20층 공동주택 = 고층 아파트).
    * 표에 없는 용도·용도 미상 = archetype None + absence(usage_not_in_archetype_table·usage_unknown) — 기본 원형 없음.
      행이 원형 없음(archetype null)을 선언하면 그 행의 absence(예 no_doe_archetype).
    * 도면으로 확인된 원형은 호출자가 이 결과보다 앞세운다(표의 precedence).
    """
    t = table if table is not None else globals().get("USAGE_ARCHETYPE")
    if t is None:
        raise LookupError("USAGE_ARCHETYPE 가 이 생성본에 없다 — gen_constants exports 에 넣는다")
    name = str(usage).strip() if usage is not None else ""
    if not name:
        return {"archetype": None, "flag": None, "absence": "usage_unknown", "basis": None}
    name = (t.get("usage_aliases") or {}).get(name, name)
    row = (t.get("rows") or {}).get(name)
    if row is None:
        return {"archetype": None, "flag": None, "absence": "usage_not_in_archetype_table", "basis": None}
    if row.get("rule") == "office_by_gross_floor_area":
        rule = t["office_by_gross_floor_area"]
        try:
            area = float(gross_floor_area_m2) if gross_floor_area_m2 is not None else None
        except (TypeError, ValueError):
            area = None
        if area is None or area != area or area <= 0:
            unk = rule["unknown_area"]
            return {"archetype": unk["archetype"], "flag": unk["flag"], "absence": None,
                    "basis": "office_by_gross_floor_area:unknown_area"}
        for band in rule["bands"]:
            lo, hi = band.get("min_m2_exclusive"), band.get("max_m2_inclusive")
            if (lo is None or area > lo) and (hi is None or area <= hi):
                return {"archetype": band["archetype"], "flag": None, "absence": None,
                        "basis": "office_by_gross_floor_area"}
        raise ValueError(f"업무시설 면적 구간이 {area} m² 를 덮지 않는다 — 표 결함")
    if row.get("rule") == "apartment_by_floors":
        rule = t["apartment_by_floors"]
        try:
            floors = int(floors_above) if floors_above is not None else None
        except (TypeError, ValueError):
            floors = None
        if floors is None or floors <= 0:
            unk = rule["unknown_floors"]
            return {"archetype": unk["archetype"], "flag": unk.get("flag"), "absence": None,
                    "basis": "apartment_by_floors:unknown_floors"}
        code = (rule["midrise_archetype"] if floors <= int(rule["midrise_max_floors_inclusive"])
                else rule["highrise_archetype"])
        return {"archetype": code, "flag": None, "absence": None, "basis": "apartment_by_floors"}
    if row.get("archetype") is None:
        return {"archetype": None, "flag": None, "absence": row.get("absence") or "usage_not_in_archetype_table",
                "basis": row.get("basis")}
    return {"archetype": row["archetype"], "flag": None, "absence": None, "basis": row.get("basis")}


def ec_percentile(values, q: float):
    """백분위수 — 선형 보간(numpy 'linear'·Excel PERCENTILE.INC), q∈[0,1]. 빈 입력·None 만 있으면 None
    (못 잼을 0 으로 올리지 않는다). q 가 [0,1] 밖이면 ValueError — 0~100 척도를 넣지 않는다."""
    if not 0.0 <= float(q) <= 1.0:
        raise ValueError(f"q 는 [0,1] 이다(받은 값 {q!r})")
    xs = sorted(float(v) for v in values if v is not None)
    if not xs:
        return None
    pos = (len(xs) - 1) * float(q)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def ec_carbon_kg(fuel_kwh: dict, factors: dict | None = None) -> float:
    """연료별 kWh → kgCO2e. 계수 = EMISSION_FACTORS_KR(`<연료>_kg_co2_per_kwh`). 모르는 연료는 KeyError
    — 혼합 계수·전력 계수로 대신 곱하지 않는다(모든 절감 kWh 에 전력 계수를 곱하던 자리)."""
    f = factors if factors is not None else globals().get("EMISSION_FACTORS_KR")
    if f is None:
        raise LookupError("EMISSION_FACTORS_KR 가 이 생성본에 없다")
    total = 0.0
    for fuel, kwh in fuel_kwh.items():
        key = f"{fuel}_kg_co2_per_kwh"
        if key not in f:
            raise KeyError(f"CARBON_FUEL_UNKNOWN: {fuel!r} (계수 {sorted(f)})")
        total += float(kwh) * float(f[key])
    return total


def ec_competition_ranks(sorted_values) -> list:
    """이미 정렬된 값의 경쟁 순위 — 같은 값은 같은 순위, 다음 순위는 건너뛴다(1,2,2,4). 처리 순서는 순위가 아니다.
    (2026-09-28 — 게이트웨이 serving/stats.competition_ranks 이관: 도구마다 동점을 입력 순서로 갈랐다)"""
    ranks: list = []
    previous: object = object()
    for index, value in enumerate(sorted_values):
        ranks.append(ranks[-1] if ranks and value == previous else index + 1)
        previous = value
    return ranks


def ec_average_ranks(values) -> list:
    """Spearman 용 순위(1부터) — 동점은 평균 순위."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def ec_tukey_fences(values, k: float | None = None, min_n: int = 1):
    """Tukey 울타리 — q1·q3 = ec_percentile(선형), 위 = q3 + k·IQR · 아래 = q1 − k·IQR.
    k 가 없으면 JUDGEMENT_THRESHOLDS.anomaly.tukey_iqr_k(생성본 전역). 값이 min_n 개 미만이면 None."""
    if k is None:
        thr = globals().get("JUDGEMENT_THRESHOLDS")
        if thr is None:
            raise LookupError("JUDGEMENT_THRESHOLDS 가 이 생성본에 없다 — k 를 인자로 준다")
        k = float(thr["anomaly"]["tukey_iqr_k"]["value"])
    xs = [float(v) for v in values if v is not None]
    if len(xs) < max(1, min_n):
        return None
    q1, q3 = ec_percentile(xs, 0.25), ec_percentile(xs, 0.75)
    iqr = q3 - q1
    return {"q1": q1, "q3": q3, "iqr": iqr, "k": float(k), "upper": q3 + k * iqr, "lower": q1 - k * iqr,
            "method": "linear_inclusive"}


def _ec_classification_table(table: dict | None) -> dict:
    t = table if table is not None else globals().get("DATA_CLASSIFICATION_VOCAB")
    if t is None:
        raise LookupError("DATA_CLASSIFICATION_VOCAB 가 이 생성본에 없다 — gen_constants exports 에 넣는다")
    return t


def ec_classification_normalize(word: object, table: dict | None = None) -> str:
    """분류 낱말 하나 → 정본 낱말(data_classification.json#default.classification). 빈칸·None·표 밖 → unknown_word.

    ⛔ 모르는 것을 measured 로 올리지 않는다(분류 없음 → 실측 기본값이던 자리 12+곳)."""
    t = _ec_classification_table(table)
    unknown = t["unknown_word"]
    text = str(word).strip().casefold() if word is not None else ""
    if not text:
        return unknown
    text = t["aliases"].get(text, text)
    return text if text in t["words"] else unknown


def ec_classification_combine(words, table: dict | None = None) -> str:
    """여러 출처 분류 → 한 낱말(composite.rule_ko 그대로). 빈 입력 → unknown."""
    t = _ec_classification_table(table)
    unknown = t["unknown_word"]
    got = {ec_classification_normalize(w, t) for w in words}
    if not got or unknown in got:
        return unknown
    if len(got) == 1:
        return next(iter(got))
    comp = t["composite"]
    if got <= set(comp["imputed_family"]):
        return "measured_with_imputed"
    if got <= set(comp["virtual_family"]):
        return "virtual"
    return "mixed"


def ec_classification_meta(word: object, table: dict | None = None) -> dict:
    """정본 낱말의 표 행(source·display_class·label_ko·virtual·measured_basis) + word."""
    t = _ec_classification_table(table)
    w = ec_classification_normalize(word, t)
    return {"word": w, **t["words"][w]}


# ── 계량 칸 물리 한계(2026-09-29 N13 · 한 벌) ─────────────────────────────────────────────────────────
#   게이트웨이 serving/meter_guard.py 와 AIROS measurement_profile 이 같은 규칙을 쓴다(두 벌이면 합계가 갈린다).
#   수는 DECLARED_ASSUMPTIONS.meter_physical_limit · JUDGEMENT_THRESHOLDS.data_quality.eui_plausible_kwh_m2.max.

def ec_meter_value_ok(v: object) -> bool:
    """칸 값 = 유한 · 음수 아님 · bool 아님."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return v == v and v not in (float("inf"), float("-inf")) and v >= 0


def ec_median(values) -> float:
    xs = sorted(float(x) for x in values)
    if not xs:
        raise ValueError("ec_median: 빈 목록")
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def ec_meter_limits(declared_assumptions: dict | None = None, judgement_thresholds: dict | None = None) -> dict:
    """상한 규칙의 수 — 인자가 없으면 생성본 전역(DECLARED_ASSUMPTIONS·JUDGEMENT_THRESHOLDS)."""
    da = declared_assumptions if declared_assumptions is not None else globals().get("DECLARED_ASSUMPTIONS")
    jt = judgement_thresholds if judgement_thresholds is not None else globals().get("JUDGEMENT_THRESHOLDS")
    if da is None or jt is None:
        raise LookupError("ec_meter_limits: DECLARED_ASSUMPTIONS·JUDGEMENT_THRESHOLDS 가 없다(생성본 밖에서는 인자로)")
    spec = da["meter_physical_limit"]
    return {"eui_max_kwh_m2_yr": float(jt["data_quality"]["eui_plausible_kwh_m2"]["max"]),
            "peak_to_mean_factor": float(spec["peak_to_mean_factor"]),
            "median_multiplier": float(spec["median_multiplier"]),
            "neighbour_jump_multiple": float(spec.get("neighbour_jump_multiple", 10.0)),
            "same_hour_median_multiple": float(spec.get("same_hour_median_multiple", 10.0))}


def ec_meter_cell_bound(values, area_m2, granularity: str, limits: dict):
    """(칸 상한 kWh 또는 None, 근거). 연면적이 있으면 연면적 × 원단위 상한 ÷ 8,760 × 배수 × 칸 시간 수,
    없으면 양수 칸 중앙값 × 중앙값 배수. 둘 다 없으면 None(검사 못 함)."""
    # 칸 하나의 최대 시간 수 — 월 칸은 31일(가장 긴 달)로 잡는다(상한은 넓게, 정상 값을 자르지 않는다). 생성본은 함수만 옮기므로 안에 둔다.
    hours = {"hourly": 1.0, "subhourly": 1.0, "daily": 24.0, "monthly": 31 * 24.0}.get(granularity, 1.0)
    if ec_meter_value_ok(area_m2) and area_m2 > 0:
        bound = float(area_m2) * limits["eui_max_kwh_m2_yr"] / 8760.0 * limits["peak_to_mean_factor"] * hours
        return bound, {"rule": "area_x_ec_eui_max", "gross_area_m2": float(area_m2),
                       "eui_max_kwh_m2_yr": limits["eui_max_kwh_m2_yr"],
                       "peak_to_mean_factor": limits["peak_to_mean_factor"], "cell_hours": hours}
    positive = [float(v) for v in values if ec_meter_value_ok(v) and v > 0]
    if not positive:
        return None, {"rule": "no_bound", "why": "연면적도 양수 칸도 없어 상한을 정하지 않았다(검사 못 함)"}
    med = ec_median(positive)
    return med * limits["median_multiplier"], {"rule": "series_median_x_declared_multiplier", "median_kwh": med,
                                               "median_multiplier": limits["median_multiplier"],
                                               "positive_cells": len(positive)}


def ec_meter_spike_indices(values, bound) -> list:
    """상한을 넘는 유효 칸 번호 — 빈 칸·음수는 급등이 아니다."""
    if bound is None:
        return []
    return [k for k, v in enumerate(values) if ec_meter_value_ok(v) and float(v) > bound]


def ec_meter_jump_indices(values, first_local_hour: int, granularity: str, limits: dict, exclude=()):
    """홀로 튄 한 칸(시간 계열만) — (칸 번호, 근거). first_local_hour = 첫 칸의 현지(KST) 시각 0~23 — 칸 k 의 시각은
    (first_local_hour + k) % 24. 걸리려면 모두: 앞뒤 칸이 있다 · 값 > 이웃 배수 × max(앞, 뒤) · 값 > 같은 시각 중앙값 배수 × 기준값
    (그 시각 양수 칸 중앙값, 계열 양수 중앙값보다 작으면 그 값). exclude = 물리 상한으로 대체할 칸(중앙값에서 빼고 이웃이면 기준값)."""
    exclude = set(exclude or ())
    if granularity not in ("hourly", "subhourly") or len(values) < 3:
        return [], {"rule": "not_applicable", "why": "홀로 튄 칸 규칙은 시간 계열에만"}
    j_mult, h_mult = limits["neighbour_jump_multiple"], limits["same_hour_median_multiple"]

    def hour(k: int) -> int:
        return (int(first_local_hour) + k) % 24

    by_hour: dict = {}
    positive: list = []
    for k, v in enumerate(values):
        if k in exclude or not ec_meter_value_ok(v) or v <= 0:
            continue
        by_hour.setdefault(hour(k), []).append(float(v))
        positive.append(float(v))
    if not positive:
        return [], {"rule": "no_reference", "why": "양수 칸이 없어 기준값을 정하지 않았다"}
    floor = ec_median(positive)
    ref = {h: max(ec_median(vs), floor) for h, vs in by_hour.items()}

    def reference(k: int) -> float:
        return ref.get(hour(k), floor)

    def neighbour(k: int):
        if k in exclude:
            return reference(k)
        v = values[k]
        return float(v) if ec_meter_value_ok(v) else None

    hits = []
    for k in range(1, len(values) - 1):
        v = values[k]
        if k in exclude or not ec_meter_value_ok(v):
            continue
        left, right = neighbour(k - 1), neighbour(k + 1)
        if left is None or right is None:
            continue
        if float(v) > j_mult * max(left, right) and float(v) > h_mult * reference(k):
            hits.append(k)
    return hits, {"rule": "isolated_neighbour_jump", "neighbour_jump_multiple": j_mult,
                  "same_hour_median_multiple": h_mult, "series_positive_median_kwh": floor}
