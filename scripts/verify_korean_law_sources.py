"""korean_building_standards.json ↔ 법령 원문 파일 대조 (2026-09-17).

무엇을 보나
  1. 출처 파일 무결성 — `sources.*.annexes.*.file` 이 있고 sha256 이 기록과 같다.
  2. 전사 정확성 — 원문 PDF 텍스트에서 숫자를 **원문 순서대로** 뽑아 스키마 값과 대조한다.
     (병합 셀은 텍스트 순서가 표의 칸 순서와 다르다 — 순서표 `_U_TEXT_ORDER` 가 그 대응을 적는다.)
     용도프로필(HWP)은 pyhwp 가 있으면 표를 읽어 23 종 전 필드를 대조한다.
  3. 현행성 기한 — `currency.retrieved + recheck_after_days` 가 지났는지.
  4. 파생 복사본 — `simulation_scenarios.ko_envelope_uvalue` 가 정본에서 파생한 값과 같은지.

⚠ 해시·조회일은 **확인 이력**이다 — 현행성 증명이 아니다. 기한이 지나면 사람이 law.go.kr 현행본을 다시
   내려받아 `docs/legal_sources/<조회일>/` 에 두고 스키마를 갱신해야 한다(자동 갱신 없음).

종료 코드: 0 통과 · 1 불일치 · 2 못 잼(원문 파일·파서 없음 — 통과가 아니다) · 3 현행성 기한 지남
사용법: python scripts/verify_korean_law_sources.py [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "energy_contracts" / "schemas" / "korean_building_standards.json"
SIM_SCN = ROOT / "energy_contracts" / "schemas" / "simulation_scenarios.json"
ZONES = ("중부1", "중부2", "남부", "제주")


def _pdf_text(path: Path) -> str:
    import pypdf  # noqa: PLC0415 — 선택 의존

    return "\n".join(pg.extract_text() for pg in pypdf.PdfReader(str(path)).pages)


def _u_text_order(env: dict) -> list[float]:
    """[별표 1] 을 텍스트로 뽑았을 때 숫자가 나오는 순서 (원문 이미지로 확인한 병합 구조)."""
    z = lambda d: [d[k] for k in ZONES]  # noqa: E731
    w, r, f, win, door = env["wall"], env["roof"], env["floor"], env["window"], env["door"]
    out = z(w["direct"]["apartment"]) + z(w["direct"]["other"]) + z(w["indirect"]["apartment"]) + z(w["indirect"]["other"])
    out += [r["direct"]["중부1"], r["direct"]["남부"], r["direct"]["제주"]]          # 중부1·중부2 병합
    out += [r["indirect"]["중부1"], r["indirect"]["남부"], r["indirect"]["제주"]]
    for side in ("direct", "indirect"):
        out += z(f[side]["floor_heating"]) + z(f[side]["no_floor_heating"])
    out += [env["interfloor_floor_heating"]]
    for side in ("direct", "indirect"):
        out += z(win[side]["apartment"])
        # 공동주택 외: 중부1 창 → (중부2·남부·제주 창=문 병합) → 중부1 문
        out += [win[side]["other"]["중부1"], win[side]["other"]["중부2"], win[side]["other"]["남부"],
                win[side]["other"]["제주"], door[side]["other"]["중부1"]]
    out += [env["apartment_entrance_fire_door"]["direct"], env["apartment_entrance_fire_door"]["indirect"]]
    return out


def _check_merged_equalities(env: dict) -> list[str]:
    """병합 셀이면 두 값이 같아야 한다 — 전사에서 한쪽만 고치는 실수를 잡는다."""
    bad = []
    for side in ("direct", "indirect"):
        if env["roof"][side]["중부1"] != env["roof"][side]["중부2"]:
            bad.append(f"roof.{side}: 중부1·중부2 병합 셀인데 값이 다르다")
        for zk in ("중부2", "남부", "제주"):
            if env["window"][side]["other"][zk] != env["door"][side]["other"][zk]:
                bad.append(f"window/door.{side}.other.{zk}: 창·문 병합 셀인데 값이 다르다")
    return bad


_HWP_CACHE: dict[str, list[dict] | None] = {}


def _profiles_from_hwp(path: Path) -> list[dict] | None:
    """HWP 변환은 느리다(수 초) — 파일 해시로 캐시한다."""
    key = hashlib.sha256(path.read_bytes()).hexdigest()
    if key not in _HWP_CACHE:
        _HWP_CACHE[key] = _parse_hwp(path)
    return copy.deepcopy(_HWP_CACHE[key])


def _parse_hwp(path: Path) -> list[dict] | None:
    try:
        from hwp5.xmlmodel import Hwp5File  # noqa: F401,PLC0415
    except Exception:
        return None
    import html
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory(dir=ROOT / "build" if (ROOT / "build").exists() else None) as td:
        # hwp5.hwp5html 에는 `__main__` 블록이 없다 — `-m` 으로 부르면 아무것도 안 하고 0 을 낸다.
        code = "import sys; from hwp5.hwp5html import main; sys.argv=['hwp5html']+sys.argv[1:]; main()"
        rc = subprocess.run([sys.executable, "-c", code, "--output", td, str(path)],
                            capture_output=True, text=True).returncode
        idx = Path(td) / "index.xhtml"
        if rc != 0 or not idx.exists():
            return None
        t = idx.read_text(encoding="utf-8")
    out = []
    for tb in re.findall(r"<table.*?</table>", t, re.S)[1:]:
        cap = re.search(r"<caption.*?</caption>", tb, re.S)
        vals = {}
        for row in re.findall(r"<tr.*?</tr>", tb, re.S):
            c = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()
                 for x in re.findall(r"<td.*?</td>", row, re.S)]
            if len(c) == 3 and c[2] and c[0] != "구분":
                vals[c[0]] = c[2]
        name = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", cap.group(0)))).strip() if cap else ""
        out.append({"name": re.sub(r"^\d+\)\s*", "", name), "vals": vals})
    return out


_PROFILE_FIELDS = {"사용시작시간": "use_start", "사용종료시간": "use_end", "운전시작시간": "operation_start",
                   "운전종료시간": "operation_end", "최소도입외기량": "min_outdoor_air_m3_per_m2h",
                   "급탕요구량": "dhw_wh_per_m2d", "조명시간": "lighting_hours", "사람": "people_heat_wh_per_m2d",
                   "작업보조기기": "equipment_heat_wh_per_m2d", "난방설정온도": "heating_setpoint_c",
                   "냉방설정온도": "cooling_setpoint_c"}


def verify(today: dt.date) -> tuple[int, list[str]]:
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))["default"]
    problems: list[str] = []
    unmeasured: list[str] = []

    for sid, src in data["sources"].items():
        for ano, ann in src["annexes"].items():
            fp = ROOT / ann["file"]
            if not fp.exists():
                unmeasured.append(f"{sid}#{ano}: 원문 파일 없음 {ann['file']}")
                continue
            if hashlib.sha256(fp.read_bytes()).hexdigest() != ann["sha256"]:
                problems.append(f"{sid}#{ano}: sha256 불일치 {ann['file']}")

    env = data["envelope_u_limits"]
    problems += _check_merged_equalities(env)
    missing = [u for u in unmeasured if "원문 파일 없음" in u]
    try:
        if missing:
            raise FileNotFoundError(missing[0])
        esdc = data["sources"]["esdc_2026_360"]["annexes"]
        text = _pdf_text(ROOT / esdc["1"]["file"])
        nums = [float(x) for x in re.findall(r"(\d\.\d{3}) 이하", text)]
        if nums != _u_text_order(env):
            problems.append(f"envelope_u_limits ≠ 원문 [별표 1] 숫자 순서 (원문 {len(nums)}개)")
        # 비고는 줄바꿈이 낱말 중간에 들어간다("경상북\n도") — 공백을 모두 지우고 **정의 전체**를 대조한다.
        #   (첫 조각만 보면 '부산광역시, 서울특별시' 같은 틀린 정의도 통과한다 — 변이 시험으로 확인)
        flat = re.sub(r"\s+", "", text)
        for zk, desc in data["climate_zones"]["definitions"].items():
            if zk != "제주" and re.sub(r"\s+", "", desc) not in flat:
                problems.append(f"climate_zones.{zk}: 비고 원문과 다름")
        t8 = _pdf_text(ROOT / esdc["8"]["file"]).replace(" ", "")
        labels = {"apartment": "공동주택", "school_classroom": "학교(교실)", "hospital_ward": "병원(병실)",
                  "assembly_seats": "관람집회시설(객석)", "lodging_room": "숙박시설(객실)", "sales": "판매시설",
                  "office": "사무소", "bathhouse": "목욕장", "swimming_pool": "수영장"}
        for k, row in data["design_indoor_conditions"]["rows"].items():
            frag = "{}{}～{}{}～{}{}～{}".format(labels[k], *row["heating_c"], *row["cooling_c"], *row["cooling_rh_pct"])
            if frag not in t8:
                problems.append(f"design_indoor_conditions.{k}: 원문 [별표 8] 에 '{frag}' 없음")
        vent = data["ventilation"]
        eq = data["sources"]["bldg_equip_rule_1614"]["annexes"]["1의6"]
        t16 = _pdf_text(ROOT / eq["file"]).replace(" ", "").replace("\n", "")
        names = {"underground_station": "지하역사", "underground_mall": "지하도상가", "culture_assembly": "나.문화및집회시설",
                 "sales": "다.판매시설", "transport": "라.운수시설", "medical": "마.의료시설", "education_research": "바.교육연구시설",
                 "welfare": "사.노유자시설", "office": "아.업무시설", "parking_per_m2": "자.자동차관련시설",
                 "funeral": "차.장례식장", "other": "카.그밖의시설"}
        for k, v in vent["multi_use_per_person_m3h"].items():
            if f"{names[k]}{v}이상" not in t16:
                problems.append(f"ventilation.multi_use_per_person_m3h.{k}={v}: 원문 [별표 1의6] 과 다름")
        sch = data["sources"]["school_health_rule_366"]["annexes"]["2"]
        if f"{vent['school']['per_person_m3h']}세제곱미터" not in _pdf_text(ROOT / sch["file"]):
            problems.append("ventilation.school: 원문 [별표 2] 과 다름")
        # [별표5] 표면 열전달저항 — 텍스트 순서: 벽 Ri, Ro간접, Ro직접 / 바닥 Ri, Ro간접, Ro직접 / 지붕 … / 층간 Ri
        sr = data["surface_resistances"]
        t5 = _pdf_text(ROOT / esdc["5"]["file"])
        got5 = [float(x) for x in re.findall(r"(\d\.\d+)\s*\(", t5)]
        want5 = []
        for part in ("wall", "lowest_floor", "top_roof"):
            want5 += [sr[part]["inside"], sr[part]["outside_indirect"], sr[part]["outside_direct"]]
        want5 += [sr["apartment_interfloor"]["inside"]]
        if got5 != want5:
            problems.append(f"surface_resistances ≠ 원문 [별표5] (원문 {got5})")
        al = data["air_layer_resistances"]
        t6 = re.sub(r"\s+", "", _pdf_text(ROOT / esdc["6"]["file"]))
        frags6 = [f"{al['factory_sealed']['per_cm_upto_cm']}cm이하{al['factory_sealed']['per_cm']}×da(cm)",
                  f"{al['factory_sealed']['per_cm_upto_cm']}cm초과{al['factory_sealed']['above']}(",
                  f"{al['site_built']['per_cm_upto_cm']}cm이하{al['site_built']['per_cm']}×da(cm)",
                  f"{al['site_built']['per_cm_upto_cm']}cm초과{al['site_built']['above']}(",
                  f"방사율0.5이하:(1)또는(2)에서계산된열저항의{al['reflective_multiplier']['emissivity_le_0_5']}배",
                  f"방사율0.1이하:(1)또는(2)에서계산된열저항의{al['reflective_multiplier']['emissivity_le_0_1']}배"]
        for fr in frags6:
            if fr not in t6:
                problems.append(f"air_layer_resistances: 원문 [별표6] 에 '{fr}' 없음")
        excerpt = ROOT / "docs" / "legal_sources" / data["currency"]["retrieved"] / "esdc_2026_360_articles_excerpt.txt"
        if excerpt.exists():
            ex = re.sub(r"\s+", "", excerpt.read_text(encoding="utf-8"))
            rules = data["envelope_surface_rules"]
            for key in ("direct", "indirect"):
                if re.sub(r"\s+", "", rules[key]) not in ex:
                    problems.append(f"envelope_surface_rules.{key}: 조문 발췌와 다름")
            for i, e in enumerate(rules["insulation_exemptions"]):
                if re.sub(r"\s+", "", e) not in ex:
                    problems.append(f"envelope_surface_rules.insulation_exemptions[{i}]: 조문 발췌와 다름")
        else:
            unmeasured.append("조문 발췌 파일 없음 — envelope_surface_rules 대조 못 잼")
        zeb = data["sources"]["zeb_criteria_2024_893"]["annexes"]["3"]
        tz = _pdf_text(ROOT / zeb["file"]).replace(" ", "")
        ac = data["assessment_conditions"]["zeb_setpoints"]
        if f"냉방{ac['cooling_c']}℃" not in tz or f"난방{ac['heating_c']}℃" not in tz:
            problems.append("assessment_conditions.zeb_setpoints: 원문 [별표 3] 과 다름")
    except ImportError:
        unmeasured.append("pypdf 없음 — PDF 원문 대조 못 잼")
    except FileNotFoundError:
        unmeasured.append("원문 파일이 없어 PDF 대조를 건너뜀")

    kea = data["sources"]["kea_zeb_rule_20260320"]["annexes"]["2"]
    rows = _profiles_from_hwp(ROOT / kea["file"]) if (ROOT / kea["file"]).exists() else None
    if rows is None:
        unmeasured.append("용도프로필 HWP 를 읽지 못함(pyhwp 없음) — 대조 못 잼")
    else:
        profs = list(data["usage_profiles"]["profiles"].values())
        if len(rows) != len(profs):
            problems.append(f"usage_profiles: 원문 {len(rows)} 종 ↔ 스키마 {len(profs)} 종")
        for r, p in zip(rows, profs):
            if r["name"] != p["name_kr"]:
                problems.append(f"usage_profiles 이름 순서: 원문 {r['name']!r} ↔ {p['name_kr']!r}")
            for kr, en in _PROFILE_FIELDS.items():
                raw = r["vals"].get(kr)
                want = raw if raw and ":" in raw else (float(raw) if raw else None)
                if want != p[en]:
                    problems.append(f"usage_profiles.{p['name_kr']}.{en}: 원문 {raw!r} ↔ {p[en]!r}")
            days = [int(r["vals"].get(f"{m}월 사용일수", -1)) for m in range(1, 13)]
            if days != p["monthly_use_days"]:
                problems.append(f"usage_profiles.{p['name_kr']}.monthly_use_days 불일치")

    sim = json.loads(SIM_SCN.read_text(encoding="utf-8"))["default"]["ko_envelope_uvalue"]
    for v in sim.values():
        z = v["_zone"]
        want = {"wall": env["wall"]["direct"]["other"][z], "roof": env["roof"]["direct"][z],
                "floor": env["floor"]["direct"]["no_floor_heating"][z], "window": env["window"]["direct"]["other"][z]}
        for k, w in want.items():
            if v[k] != w:
                problems.append(f"simulation_scenarios.ko_envelope_uvalue.{z}.{k}={v[k]} ≠ 정본 파생 {w}")

    cur = data["currency"]
    due = dt.date.fromisoformat(cur["retrieved"]) + dt.timedelta(days=int(cur["recheck_after_days"]))
    if problems:
        return 1, problems + unmeasured
    if unmeasured:
        return 2, unmeasured
    if today > due:
        return 3, [f"현행성 확인 기한 {due} 지남 — law.go.kr 현행본 재확인 필요"]
    return 0, [f"OK — 원문 대조 통과 · 현행성 기한 {due}"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=None)
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    rc, msgs = verify(today)
    for m in msgs:
        print(("  " if rc else "") + m)
    return rc


if __name__ == "__main__":
    sys.exit(main())
