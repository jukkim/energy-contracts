# -*- coding: utf-8 -*-
"""선언 어휘 적재 검사(0.3.72) — **한 별칭 = 한 열쇠** · **가리키는 열쇠는 정본에 있다**.

별칭·어휘 표(조치 별칭 · 설비 종류 이름 · 자산 종류 이름 · 분류 낱말 별칭 · 시설 종류 이름 · 전송 주기 이름 · 사건 명사)가
두 열쇠를 같은 말로 부르면 소비처가 조용히 한쪽을 고른다. 표가 없는 열쇠를 가리키면 소비처가 조용히 건너뛴다.
둘 다 **적재 때** 막는다 — 호출하는 곳은 둘이고 규칙은 여기 한 곳이다:

* ``gen_constants.load_schemas`` — 결함이 있으면 생성하지 않는다(ValueError).
* ``validate_ssot.py --check schemas`` — 커밋 게이트.

어휘 표는 **손으로 적지 않고 찾는다**: 스키마 ``default`` 를 훑어 ``aliases_ko``·``names_ko`` 를 가진 항목들의 묶음(그 묶음이 한 어휘)과
``aliases_ko`` 라는 이름의 {열쇠: [말…]} 표를 모두 어휘로 본다 — 새 어휘 칸이 생기면 저절로 검사 대상이 된다.
가리키는 열쇠의 모집단도 정본에서 읽는다(설비 종류 = ``capability_matrix`` · 분류 낱말 = ``ClassificationWord`` · 용도 = ``EndUse`` …).

반환 = (결함 목록, 검사 수). 검사 수 0 은 통과가 아니다(부르는 쪽이 사고로 센다).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator

#: 한 항목의 '부르는 말' 칸 — 문자열 칸 · 목록 칸
NAME_FIELDS = ("name_ko", "label_ko", "name")
LIST_FIELDS = ("aliases_ko", "names_ko")
SIGNATURE_OPS = ("lt", "le", "gt", "ge", "within")
QUESTION_SEASONS = ("spring", "summer", "autumn", "winter")


def norm(term: object) -> str:
    """대조 열쇠 — 띄어쓰기를 지우고 대소문자를 접는다('시스템 에어컨' = '시스템에어컨' · 'EHP' = 'ehp')."""
    return re.sub(r"\s+", "", str(term)).casefold()


def collisions(table: dict[str, Iterable[str]]) -> tuple[list[str], int]:
    """{열쇠: [말…]} → (한 말(정규화)이 두 열쇠를 가리키는 자리, 대조한 말 수). 같은 열쇠 안의 겹침(띄어쓰기 변형)은 허용한다."""
    owner: dict[str, str] = {}
    out: list[str] = []
    n = 0
    for key, terms in table.items():
        for term in terms:
            n += 1
            k = norm(term)
            if not k:
                out.append(f"{key}: 빈 말")
                continue
            prev = owner.setdefault(k, key)
            if prev != key:
                out.append(f"'{term}' → {prev} · {key}")
    return out, n


def _terms_of(key: str, entry: dict) -> list[str]:
    terms = [key]
    terms += [entry[f] for f in NAME_FIELDS if isinstance(entry.get(f), str)]
    for f in LIST_FIELDS:
        terms += [str(t) for t in (entry.get(f) or []) if isinstance(entry.get(f), list)]
    return terms


def discover(node: Any, path: str = "") -> Iterator[tuple[str, dict[str, list[str]]]]:
    """스키마 default 안의 어휘 표 전부 — (자리, {열쇠: [말…]}). 손 목록 없음."""
    if isinstance(node, dict):
        entries = {k: v for k, v in node.items() if isinstance(v, dict)}
        if any(isinstance(v.get(f), list) for v in entries.values() for f in LIST_FIELDS):
            yield path or "/", {k: _terms_of(k, v) for k, v in entries.items()}
        if path.endswith("/aliases_ko") and node and all(isinstance(v, list) for v in node.values()):
            yield path, {k: [k, *v] for k, v in node.items()}
        for k, v in node.items():
            yield from discover(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from discover(v, f"{path}[{i}]")


def _load_dir(schemas_dir: Path) -> dict[str, dict]:
    return {fp.stem: json.loads(fp.read_text(encoding="utf-8")) for fp in sorted(Path(schemas_dir).glob("*.json"))}


def problems(docs: dict[str, dict]) -> tuple[list[str], int]:
    """모든 스키마 문서 {이름: 문서} → (결함, 검사 수)."""
    out: list[str] = []
    checks = 0

    # ① 한 별칭 = 한 열쇠 — 어휘 표는 찾아서
    for name, doc in docs.items():
        for where, table in discover(doc.get("default"), ""):
            bad, n = collisions(table)
            checks += n
            out += [f"{name}{where}: 별칭 겹침 {b}" for b in bad]

    def d(name: str) -> dict:
        return (docs.get(name) or {}).get("default") or {}

    # ② 가리키는 열쇠가 정본에 있다 — 모집단은 정본에서
    equip = d("equipment_taxonomy")
    kinds = set(equip.get("capability_matrix") or {})
    if equip.get("aliases_ko") is not None or equip.get("labels_ko") is not None or equip.get("dr_class") is not None:
        checks += 1
        if not kinds:
            out.append("equipment_taxonomy: capability_matrix 가 비었다 — 종류 열쇠를 대조할 모집단 없음")
        for field in ("aliases_ko", "labels_ko"):
            unknown = sorted(set(equip.get(field) or {}) - kinds)
            checks += len(equip.get(field) or {})
            if unknown:
                out.append(f"equipment_taxonomy.{field}: capability_matrix 에 없는 종류 {unknown}")
        labels = equip.get("labels_ko") or {}
        for kind, words in (equip.get("aliases_ko") or {}).items():       # 질문 말 이름표는 채널 이름표를 모두 담는다(두 벌이 갈리지 않게)
            checks += 1
            spec = labels.get(kind)
            have = {norm(spec.get("name_ko", ""))} | {norm(w) for w in (spec.get("aliases_ko") or [])} if isinstance(spec, dict) else set()
            missing = [w for w in words if norm(w) not in have]
            if labels and missing:
                out.append(f"equipment_taxonomy.labels_ko.{kind}: aliases_ko[{kind}] 의 {missing} 가 없다")
        dr = equip.get("dr_class")
        if dr is not None:
            classes = set((dr.get("classes") or {}))
            by_kind = dr.get("by_kind") or {}
            checks += len(by_kind) + len(dr.get("by_end_use") or {})
            if sorted(set(by_kind) - kinds):
                out.append(f"equipment_taxonomy.dr_class.by_kind: capability_matrix 에 없는 종류 {sorted(set(by_kind) - kinds)}")
            bad = sorted({v for v in [*by_kind.values(), *(dr.get("by_end_use") or {}).values()] if v not in classes})
            if bad:
                out.append(f"equipment_taxonomy.dr_class: classes 에 없는 분류 {bad}")
            decl = d("declared_assumptions")
            for cls, spec in (dr.get("classes") or {}).items():
                ref = (spec or {}).get("share_ref")
                if ref:
                    checks += 1
                    schema, key = ref.split(".", 1)
                    if key not in d(schema):
                        out.append(f"equipment_taxonomy.dr_class.classes.{cls}.share_ref={ref} 가 없는 행을 가리킨다")
                    elif schema == "declared_assumptions" and "value" not in decl.get(key, {}):
                        out.append(f"equipment_taxonomy.dr_class.classes.{cls}.share_ref={ref} 행에 value 가 없다")

    decl = d("declared_assumptions")
    comm = decl.get("comm_status_thresholds") or {}
    if comm:
        by_delivery = comm.get("by_delivery") or {}
        checks += len(by_delivery) + 1
        unlabelled = sorted(p for p, spec in by_delivery.items() if not str((spec or {}).get("label_ko") or "").strip())
        if by_delivery and any("label_ko" in (s or {}) for s in by_delivery.values()) and unlabelled:
            out.append(f"comm_status_thresholds.by_delivery: 이름(label_ko) 없는 전송 주기 {unlabelled}")
        bad, n = collisions({p: [s.get("label_ko")] for p, s in by_delivery.items() if (s or {}).get("label_ko")})
        checks += n
        out += [f"comm_status_thresholds.by_delivery 이름 겹침 {b}" for b in bad]
        if comm.get("unknown_delivery_profile") not in by_delivery:
            out.append("comm_status_thresholds.unknown_delivery_profile 이 by_delivery 에 없다")

    ev = (decl.get("schedule_event_nouns") or {}).get("value")
    if ev is not None:
        lists = {f: list(ev.get(f) or []) for f in ("nouns", "nouns_needing_date_word", "date_words")}
        checks += sum(len(v) for v in lists.values())
        if not lists["nouns"] or not lists["date_words"]:
            out.append("schedule_event_nouns: nouns · date_words 가 비었다")
        for f, words in lists.items():
            dup = sorted({w for w in words if [norm(x) for x in words].count(norm(w)) > 1})
            if dup:
                out.append(f"schedule_event_nouns.{f}: 겹친 말 {dup}")
        bad, _ = collisions({"noun": lists["nouns"], "noun_needing_date_word": lists["nouns_needing_date_word"],
                             "date_word": lists["date_words"]})
        out += [f"schedule_event_nouns: 한 말이 두 칸에 {b}" for b in bad]

    fac = (decl.get("facility_use_classes") or {}).get("value")
    if fac is not None:
        words = set(((docs.get("data_classification") or {}).get("$defs") or {}).get("ClassificationWord", {}).get("enum") or [])
        for cls, spec in fac.items():
            checks += 1
            if not (spec.get("uses") or spec.get("use_prefixes")):
                out.append(f"facility_use_classes.{cls}: 용도 코드(uses·use_prefixes)가 비었다")
            if any(not re.fullmatch(r"[0-9A-Z][0-9]{4}", str(u)) for u in spec.get("uses") or []):
                out.append(f"facility_use_classes.{cls}.uses 형식(주용도 코드 5자리)이 아니다: {spec.get('uses')}")
            if any(not re.fullmatch(r"[0-9]{2}", str(p)) for p in spec.get("use_prefixes") or []):
                out.append(f"facility_use_classes.{cls}.use_prefixes 형식(대분류 2자리)이 아니다: {spec.get('use_prefixes')}")
            if spec.get("classification") not in words:
                out.append(f"facility_use_classes.{cls}.classification={spec.get('classification')!r} 는 ClassificationWord 가 아니다")

    personas = (decl.get("debate_default_personas") or {}).get("value") or {}
    fam = (decl.get("debate_family_critics") or {}).get("value")
    if fam is not None:
        old = personas.get("critics_by_family") or {}
        known_critics = {c for cs in old.values() for c in cs}
        checks += len(fam)
        both = sorted(set(fam) & set(old))
        if both:
            out.append(f"debate_family_critics: debate_default_personas.critics_by_family 에도 있는 가족 {both}(EC_ROW_DRIFT)")
        unknown_fam = sorted(set(fam) - set(personas.get("by_family") or {}))
        if unknown_fam:
            out.append(f"debate_family_critics: debate_default_personas.by_family 에 없는 가족 {unknown_fam}")
        unknown_critic = sorted({c for cs in fam.values() for c in cs} - known_critics)
        if unknown_critic:
            out.append(f"debate_family_critics: 정본 Critic 구성에 없는 이름 {unknown_critic}")

    catalog = docs.get("measure_cost_catalog") or {}
    measures = (catalog.get("default") or {}).get("measures") or {}
    demo = (decl.get("demo_user_answers") or {}).get("value")
    if demo is not None:
        checks += 1
        if demo.get("replacement_measure_code") not in measures:
            out.append(f"demo_user_answers.replacement_measure_code={demo.get('replacement_measure_code')!r} 가 조치 목록에 없다")

    shift = (decl.get("climate_load_shift") or {}).get("value")
    if shift is not None:
        end_uses = set(((catalog.get("$defs") or {}).get("EndUse") or {}).get("enum") or [])
        for scen, mult in shift.items():
            checks += 1
            bad = sorted(set(mult) - end_uses)
            if bad:
                out.append(f"climate_load_shift.{scen}: EndUse 에 없는 용도 {bad}")

    hws = (decl.get("hazard_week_scenarios") or {}).get("value")
    if hws is not None:
        for hazard, rows in hws.items():
            checks += 1
            if hazard not in (decl.get("hazard_days") or {}):
                out.append(f"hazard_week_scenarios.{hazard}: hazard_days 에 없는 위험")
            ids = [r.get("id") for r in rows]
            if len(set(ids)) != len(ids):
                out.append(f"hazard_week_scenarios.{hazard}: 시나리오 id 겹침 {ids}")

    strategies = d("ems_strategies").get("strategies") or {}
    metrics: dict[str, str] = {}
    for code, meta in strategies.items():
        sig = (meta or {}).get("observable_signature")
        if sig is None:
            continue
        checks += 1
        if sig.get("op") not in SIGNATURE_OPS:
            out.append(f"ems_strategies.{code}.observable_signature.op={sig.get('op')!r}")
        thr = sig.get("threshold")
        if sig.get("op") == "within" and not (isinstance(thr, list) and len(thr) == 2 and thr[0] <= thr[1]):
            out.append(f"ems_strategies.{code}.observable_signature: within 의 threshold 는 [하한, 상한]")
        prev = metrics.setdefault(str(sig.get("metric")), code)
        if prev != code:
            out.append(f"ems_strategies.observable_signature.metric '{sig.get('metric')}' 가 {prev} · {code} 둘에")

    # ── 0.3.74(2026-10-01 · 캠페인 요청 EC_ROWS_NEEDED_round3): 새 어휘 칸이 가리키는 열쇠 ─────────────────────────────────────
    #   요금 종별(원형 전기 · 자산 종류 가스) · 설정온도 동작 · 적용 전제 · 조합 쉬운 이름 · 용도→원형 관계. 소비처는 모르는 열쇠를 만나면
    #   조용히 참조 단가·'전제 없음'으로 떨어진다 — 그래서 적재 때 막는다(규칙 한 곳 · 반례 = tests/test_ec_rows_0374.py).
    out_0374, n_0374 = _problems_0374(d, docs.get("building_usage_map"))
    out += out_0374
    checks += n_0374

    cal = d("calendar_conventions")
    chosen = cal.get("question_season_system")
    if chosen is not None:
        checks += 1
        seasons = ((cal.get("season_systems") or {}).get(chosen) or {}).get("seasons")
        if not isinstance(seasons, dict):
            out.append(f"calendar_conventions.question_season_system={chosen!r} 는 계절 표(seasons)를 가진 체계가 아니다")
        else:
            lacking = [s for s in QUESTION_SEASONS if s not in seasons]
            months = sorted(m for ms in seasons.values() for m in ms)
            if lacking:
                out.append(f"calendar_conventions.question_season_system={chosen!r} 에 계절 {lacking} 가 없다")
            if months != list(range(1, 13)):
                out.append(f"calendar_conventions.question_season_system={chosen!r} 가 1~12월을 한 번씩 덮지 않는다")
    return out, checks


def _class_keys(table: Any) -> set[str]:
    """종별 표({열쇠: {label_ko, market_prices_ref …}, rule_ko, source …}) → 종별 열쇠(항목이 사전인 것만)."""
    return {k for k, v in (table or {}).items() if isinstance(v, dict)}


def _walk(node: Any, dotted: str) -> Any:
    for part in str(dotted).split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _problems_0374(d, usage_doc: dict | None = None) -> tuple[list[str], int]:
    """0.3.74 어휘 칸 검사 — ``d(name)`` = 그 스키마의 default · ``usage_doc`` = building_usage_map 문서 전체(대상 사실 칸의 선언). (결함, 검사 수)."""
    out: list[str] = []
    checks = 0
    tv, ba, ems, um = d("target_vocabulary"), d("building_archetypes"), d("ems_strategies"), d("building_usage_map")
    market = d("market_prices")

    # ① 요금 종별 — 원형 전기 종별 · 자산 종류 가스 종별이 종별 표의 열쇠이고, 종별 표의 market_prices_ref 가 수를 가리킨다
    elec = _class_keys(tv.get("electricity_price_classes"))
    gas = _class_keys(tv.get("gas_price_classes"))
    for name, table in (("electricity_price_classes", tv.get("electricity_price_classes")), ("gas_price_classes", tv.get("gas_price_classes"))):
        for key in _class_keys(table):
            checks += 1
            ref = (table[key] or {}).get("market_prices_ref")
            value = _walk(market, ref) if ref else None
            number = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)  # noqa: E731
            # 달이 필요한 종별(needs_month — 계절 단가 표)은 수를 담은 표 · 그 밖은 수 하나
            ok = (isinstance(value, dict) and any(number(v) for v in value.values())) if (table[key] or {}).get("needs_month") else number(value)
            if not ok:
                out.append(f"target_vocabulary.{name}.{key}.market_prices_ref={ref!r} 가 market_prices 의 수(계절 종별이면 수 표)를 가리키지 않는다")
    docs = ba.get("doe_buildings") or {}
    with_class = {c: m.get("electricity_price_class") for c, m in docs.items() if "electricity_price_class" in (m or {})}
    if with_class:
        checks += len(docs)
        lacking = sorted(set(docs) - set(with_class))
        if lacking:
            out.append(f"building_archetypes.doe_buildings: electricity_price_class 가 없는 원형 {lacking}(한 원형만 빠지면 소비처가 조용히 참조 단가로 떨어진다)")
        bad = sorted(c for c, v in with_class.items() if v not in elec)
        if bad:
            out.append(f"building_archetypes.doe_buildings.electricity_price_class: electricity_price_classes 에 없는 종별 {[(c, with_class[c]) for c in bad]}")
    kinds = tv.get("air_asset_kinds") or {}
    if any("gas_price_class" in (k or {}) for k in kinds.values()):
        checks += len(kinds)
        for kind, spec in kinds.items():
            if "gas_price_class" not in (spec or {}):
                out.append(f"target_vocabulary.air_asset_kinds.{kind}: gas_price_class 칸이 없다(null = 참조 단가 — 칸이 없으면 선언 없음)")
            elif spec["gas_price_class"] is not None and spec["gas_price_class"] not in gas:
                out.append(f"target_vocabulary.air_asset_kinds.{kind}.gas_price_class={spec['gas_price_class']!r} 가 gas_price_classes 에 없다")

    # ② 전략 — 설정온도 동작 · 적용 전제 · 쉬운 이름
    strategies = ems.get("strategies") or {}
    actions = set(((ems.get("setpoint_actions") or {}).get("values") or {}))
    conditions = (ems.get("applicability_conditions") or {}).get("values") or {}
    # 전제를 가르는 대상 사실 = 용도 항목 스키마(UsageEntry)가 참·거짓 칸으로 선언한 이름(예 operates_24h)
    entry_props = (((usage_doc or {}).get("$defs") or {}).get("UsageEntry") or {}).get("properties") or {}
    usage_facts = {k for k, spec in entry_props.items() if isinstance(spec, dict) and spec.get("type") == "boolean"}
    if ems.get("setpoint_actions") is not None:
        for code, meta in strategies.items():
            checks += 1
            act = (meta or {}).get("setpoint_action")
            if meta.get("type") == "combined":
                if act is not None:
                    out.append(f"ems_strategies.{code}: 조합 전략에 setpoint_action={act!r} — 조합은 구성 대책에서 파생한다(싣지 않는다)")
            elif act not in actions:
                out.append(f"ems_strategies.{code}.setpoint_action={act!r} 가 setpoint_actions.values 에 없다")
    for code, meta in strategies.items():
        for cond in (meta or {}).get("applies_when") or []:
            checks += 1
            if cond not in conditions:
                out.append(f"ems_strategies.{code}.applies_when: applicability_conditions.values 에 없는 전제 {cond!r}")
    for cond, spec in conditions.items():
        checks += 1
        fact = (spec or {}).get("decided_by_usage_fact")
        if fact is not None and fact not in usage_facts:
            out.append(f"ems_strategies.applicability_conditions.{cond}.decided_by_usage_fact={fact!r} 를 선언한 용도가 building_usage_map.usages 에 없다")
        if fact is not None and not isinstance((spec or {}).get("met_when_fact_is"), bool):
            out.append(f"ems_strategies.applicability_conditions.{cond}: met_when_fact_is 가 참·거짓이 아니다")
    rule = ems.get("easy_name_rule")
    if rule is not None:
        prefix, joiner = str(rule.get("combined_prefix_ko") or ""), str(rule.get("joiner_ko") or "")
        names: dict[str, str] = {}
        for code, meta in strategies.items():
            checks += 1
            easy = (meta or {}).get("easy_name_kr")
            if not isinstance(easy, str) or not easy.strip():
                out.append(f"ems_strategies.{code}: easy_name_kr 가 비었다")
                continue
            if meta.get("type") == "combined":
                want = prefix + joiner.join(str((strategies.get(c) or {}).get("easy_name_kr")) for c in meta.get("components") or [])
                if easy != want:
                    out.append(f"ems_strategies.{code}.easy_name_kr 가 구성 대책의 쉬운 이름을 이은 글과 다르다: {easy!r} ≠ {want!r}")
            names[code] = easy
        bad, n = collisions({c: [e] for c, e in names.items()})
        checks += n
        out += [f"ems_strategies.easy_name_kr 이름 겹침 {b}" for b in bad]

    # ③ 용도 → 원형 관계 — 원형(또는 규칙)이 있는 행마다 관계 어휘의 열쇠 · 원형 없음 행에는 없다
    ua = um.get("usage_archetype") or {}
    relations = set(((ua.get("archetype_relations") or {}).get("values") or {}))
    if relations:
        for usage, row in (ua.get("rows") or {}).items():
            checks += 1
            has_target = bool((row or {}).get("archetype") or (row or {}).get("rule"))
            rel = (row or {}).get("archetype_relation")
            if has_target and rel not in relations:
                out.append(f"building_usage_map.usage_archetype.rows[{usage}].archetype_relation={rel!r} 가 archetype_relations.values 에 없다")
            if not has_target and rel is not None:
                out.append(f"building_usage_map.usage_archetype.rows[{usage}]: 원형 없음 행에 archetype_relation={rel!r}(대상 아님 — 싣지 않는다)")

    # ④ 선언 가정이 가리키는 계절 체계
    fresh = (d("declared_assumptions").get("operation_reading_freshness") or {}).get("value")
    if fresh is not None:
        checks += 1
        ref = str(fresh.get("season_system_ref") or "")
        schema, _, key = ref.partition(".")
        # 가리키는 칸이 **있는가**만 본다 — 체계가 아직 null(미정)이면 소비처가 판정하지 않는다(못 잼 — 0.3.72 시험이 null 을 통과시킨다)
        if not key or key not in d(schema):
            out.append(f"declared_assumptions.operation_reading_freshness.season_system_ref={ref!r} 가 계절 체계 칸을 가리키지 않는다")
        if not isinstance(fresh.get("max_season_lag"), int) or isinstance(fresh.get("max_season_lag"), bool) or fresh["max_season_lag"] < 0:
            out.append("declared_assumptions.operation_reading_freshness.max_season_lag 가 0 이상의 정수가 아니다")
    return out, checks


def problems_in_dir(schemas_dir: Path) -> tuple[list[str], int]:
    return problems(_load_dir(schemas_dir))
