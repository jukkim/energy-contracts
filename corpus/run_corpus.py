"""
run_corpus.py — 질의 코퍼스 단일 진입점 + 능력 원장(Capability Ledger) 산출
================================================================================
사용자 요구: "무언가 수정이 발생하는 경우에 테스트 셋트를 전수 수행하고 싶다."
            "능력이 확장되면 진짜 가능한 범위부터 시험해서 파악하고 적용해야 한다."

이 러너가 그 '전수 수행'의 단일 진입점이며, 결과를 **파일로 확정**한다(능력 원장).
AI 챔피언·lab·be-3d·studio·gateway 어디서든 `python <path>/corpus/run_corpus.py --all`.

코퍼스 = corpus/query_corpus.generated.json (gen_corpus.py 병합본).
실행 = gateway :8030 / studio :3040 / be-3d :8000 을 HTTP 로 호출(각 repo 소유 서비스 무이동).

Suite(7):
  class      — queryClasses(C/S/L 24) 라우팅/컴파일          [gateway+studio]
  opcode     — A/C opProbes 대표질의 라우팅 conformance      [gateway+studio]
  capability — capabilityProbes(7 executor) 라우팅 hit       [gateway]
  refuse     — refuseProbes(off-domain) refuse 게이트 회귀    [gateway]
  combo      — region×metric / bldg×sp×climate 데이터 완전성 [be-3d+studio+gateway]
  scenario   — B-op public_scenarios 재생 가능성(등록 존재)  [be-3d]
  static     — gen_corpus --check (drift 0) + 커버리지 게이트 [오프라인, 서비스 불요]

능력 4층(절차서 §1): D 선언 / R 도달 / E 실행 / G 근거.
  · class·opcode·capability·refuse = **R**(자연어에서 그 능력에 도달하는가)
  · combo                          = **G**(그 셀에 데이터가 있는가) + E 표본교차
  · scenario                       = **E**(재생 표면이 등록돼 있는가)
  · static                         = **D**(선언 정합·커버리지)

⚠ UNKNOWN 격리(절차서 §1.3): 서비스 다운·타임아웃은 FAIL 이 아니라 **UNKNOWN**.
   인프라 장애를 능력 부재로 오독하면 멀쩡한 기능을 스스로 지운다(5090 다운 → compose 롤백 전례).
   UNKNOWN 비율이 임계를 넘으면 그 스윕은 **무효**로 처리하고 원장을 쓰지 않는다.

Usage:
  python corpus/run_corpus.py --all --sweep full --report capability_ledger.json
  python corpus/run_corpus.py --suite static            # 서비스 없이 정적 게이트(CI/prebuild)
  python corpus/run_corpus.py --changed <file>...       # git diff 파일 → 영향 suite 자동
  python corpus/run_corpus.py --all --baseline capability_ledger.json   # 회귀 판정
  python corpus/run_corpus.py --sweep full --suite combo --jobs 8

Exit: 0 = 정상 / 1 = FAIL 존재·static drift·**능력 회귀**(GREEN→RED) / 2 = 스윕 무효(UNKNOWN 과다)
설계 정본: energy-decision-studio/docs/QUERY_CORPUS_SSOT.md
절차 정본: 공모전/…AI챔피언…/docs/CAPABILITY_DISCOVERY_PROCEDURE.md
"""
from __future__ import annotations
import sys, json, time, argparse, subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
CORPUS_JSON = HERE / "query_corpus.generated.json"
LEDGER_JSON = HERE / "capability_ledger.json"
GEN = HERE / "gen_corpus.py"

DEFAULT_GATEWAY = "http://localhost:8030"
DEFAULT_STUDIO  = "http://localhost:3040"
DEFAULT_BE3D    = "http://localhost:8000"

ICON = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "──", "UNKNOWN": "❔"}

# suite 판정 → 원장 상태(절차서 §1.1)
#   GREEN  = 4층 통과, 시연·제안 가능
#   AMBER  = 쓰이되 정직 문구 동반(부분/추정 데이터, 기대 op 불일치)
#   RED    = 불가(제안 금지)
#   UNKNOWN= 판정 실패(서비스 다운) — RED 로 강등 금지
LEDGER_STATUS = {"PASS": "GREEN", "WARN": "AMBER", "FAIL": "RED",
                 "SKIP": "SKIP", "UNKNOWN": "UNKNOWN"}

# 커버리지(G층) 상태 → 원장 상태 + 사유
COVERAGE_STATUS = {
    "ok":            ("GREEN", None),
    "sparse":        ("AMBER", "PARTIAL_DATA"),
    "estimate_only": ("AMBER", "ESTIMATE_ONLY"),
    "no_data":       ("RED",   "NO_DATA"),
}

UNKNOWN_ABORT_RATIO = 0.05     # 이 비율 초과면 스윕 무효(절차서 §1.3)
RETRIES = 3


# ── HTTP (재시도 + 연결오류/HTTP오류 구분) ──────────────────────────────────────
def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(2 ** attempt * 0.4, 3.0))


def _post(url: str, payload: dict, timeout: int) -> dict:
    """POST. 연결 실패는 재시도 후 `_url_error`(=UNKNOWN 사유)로 반환."""
    data = json.dumps(payload).encode("utf-8")
    last = {}
    for attempt in range(RETRIES):
        req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except HTTPError as e:                      # 서버가 응답함 = 판정 가능
            if e.code == 429 and attempt < RETRIES - 1:
                time.sleep(2.0 + attempt)           # 429 는 '지금 말고 나중에' — 유일한 재시도 대상
                continue
            return {"_http_error": e.code, "_body": e.read().decode("utf-8", "replace")[:160]}
        except (URLError, OSError) as e:
            last = {"_url_error": str(e)}
        except Exception as e:
            last = {"_error": str(e)}
        if attempt < RETRIES - 1:
            _sleep_backoff(attempt)
    return last


def _get(url: str, timeout: int) -> int:
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as r:
            return r.status
    except HTTPError as e:
        return e.code
    except Exception:
        return 0


def _get_json(url: str, timeout: int, retries: int = RETRIES):
    """(status, body). status 0 = 연결 실패(UNKNOWN 사유). HTTP 오류는 재시도 안 함."""
    last = (0, {})
    for attempt in range(retries):
        try:
            with urlopen(Request(url, method="GET"), timeout=timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2.0 + attempt)           # rate-limit 은 재시도(능력 부재 아님)
                continue
            try:
                return e.code, json.loads(e.read().decode("utf-8"))
            except Exception:
                return e.code, {}
        except Exception as e:
            last = (0, {"_err": str(e)})
        if attempt < retries - 1:
            _sleep_backoff(attempt)
    return last


def _unreachable(resp: dict) -> bool:
    return isinstance(resp, dict) and ("_url_error" in resp or "_error" in resp)


def _ops_from_compose(raw):
    try:
        ir = json.loads(raw) if isinstance(raw, str) else {}
    except Exception:
        s = (raw or "").strip().strip("```json").strip("```").strip()
        try:
            ir = json.loads(s)
        except Exception:
            ir = {}
    return ir.get("ops", []), ir.get("capability_request")


# ── 셀(cell) ────────────────────────────────────────────────────────────────
def C(cid, status, note, *, query=None, axis=None, reason=None, evidence=None, layer=None):
    """원장 셀 하나. suite 는 러너가 채운다."""
    return {"id": cid, "status": status, "note": note, "query": query,
            "axis": axis or {}, "reason": reason, "evidence": evidence or {}, "layer": layer}


def _normalize(row) -> dict:
    """레거시 3-튜플도 받아들인다(점진 이행)."""
    if isinstance(row, dict):
        return row
    cid, st, note = row
    return C(cid, st, note)


# ── 케이스 판정 ─────────────────────────────────────────────────────────────
def _judge_cap(query, expect, refuse_ok, gw, timeout):
    resp = _post(f"{gw}/v1/capability-route", {"query": query}, timeout)
    if _unreachable(resp):
        return "UNKNOWN", f"gateway 미응답: {str(resp)[:50]}", "SERVICE_DOWN", {}
    err = resp.get("_http_error")
    if err:
        # 5xx·429 = 서버 사정(일시) → UNKNOWN. 4xx = 계약 위반 → FAIL.
        #   전자를 RED 로 적으면 과부하 한 번이 '능력 없음'으로 원장에 박힌다(§1.3 과 같은 원칙).
        if err >= 500 or err == 429:
            return "UNKNOWN", f"HTTP {err}(일시)", "SERVICE_DOWN" if err >= 500 else "RATE_LIMIT", {"http": err}
        return "FAIL", f"HTTP {err}", "HTTP_ERROR", {"http": err}
    ops = resp.get("ops", [])
    refuse = resp.get("refuse", False)
    got = [op.get("api", "") for op in ops]
    ev = {"ops": got, "refuse": refuse}
    if refuse:
        return (("PASS", "refuse=OK", "ESCALATE_BY_DESIGN", ev) if refuse_ok
                else ("FAIL", "refuse=True", "NL_UNREACHABLE", ev))
    if not ops:
        return (("PASS", "ops empty(refuse_ok)", "ESCALATE_BY_DESIGN", ev) if refuse_ok
                else ("FAIL", "ops empty", "NL_UNREACHABLE", ev))
    if expect and not any(a in got for a in expect):
        return "WARN", f"got={got} want∈{expect}", "MISROUTED", ev
    return "PASS", f"ops={got}", None, ev


def _judge_compose(query, expect, refuse_ok, studio, timeout):
    resp = _post(f"{studio}/api/compose", {"query": query}, timeout)
    if _unreachable(resp):
        return "UNKNOWN", f"studio 미응답: {str(resp)[:50]}", "SERVICE_DOWN", {}
    err = resp.get("_http_error")
    if err:
        if err >= 500 or err == 429:      # compose 과부하·일시 오류를 능력 부재로 적지 않는다
            return "UNKNOWN", f"HTTP {err}(일시)", "SERVICE_DOWN" if err >= 500 else "RATE_LIMIT", {"http": err}
        return "FAIL", f"HTTP {err}", "HTTP_ERROR", {"http": err}
    ops, cap_req = _ops_from_compose(resp.get("response", ""))
    got = [op.get("api", op.get("op", "")) for op in ops]
    ev = {"ops": got}
    if not ops:
        if refuse_ok:
            name = cap_req.get("suggested_name") if isinstance(cap_req, dict) else None
            return "PASS", (f"empty+capability_request={name}" if name else "empty(refuse_ok)"), \
                   "ESCALATE_BY_DESIGN", ev
        return "FAIL", f"empty raw={resp.get('response','')[:50]}", "NL_UNREACHABLE", ev
    if expect and not any(a in got for a in expect):
        return "WARN", f"got={got} want∈{expect}", "MISROUTED", ev
    return "PASS", f"ops={got}", None, ev


def _pmap(fn, items, jobs):
    """순서 보존 병렬 map(하나가 죽어도 나머지는 계속)."""
    if jobs <= 1:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        return list(ex.map(fn, items))


# ── Suites ───────────────────────────────────────────────────────────────────
def suite_class(corpus, ctx):
    def one(c):
        rt = c["route"]
        if rt == "cap":
            st, note, reason, ev = _judge_cap(c["query"], c["expectAny"], c["refuseOk"],
                                              ctx["gw"], ctx["timeout"])
        elif rt == "compose":
            if not ctx["compose"]:
                st, note, reason, ev = "SKIP", "--compose 미지정", None, {}
            else:
                st, note, reason, ev = _judge_compose(c["query"], c["expectAny"], c["refuseOk"],
                                                      ctx["studio"],
                                                      ctx.get("compose_timeout", ctx["timeout"]))
        elif rt == "ops_status":
            code = _get(f"{ctx['studio']}/api/ops-status", ctx["timeout"])
            if code == 200:
                st, note, reason, ev = "PASS", "HTTP 200", None, {"http": code}
            elif code == 0:
                st, note, reason, ev = "UNKNOWN", "studio 미응답", "SERVICE_DOWN", {}
            else:
                st, note, reason, ev = "FAIL", f"HTTP {code}", "HTTP_ERROR", {"http": code}
        else:
            st, note, reason, ev = "SKIP", f"route={rt}", None, {}
        return C(c["id"], st, note, query=c["query"], reason=reason, evidence=ev, layer="R")
    return _pmap(one, corpus["queryClasses"], ctx["jobs"])


def suite_opcode(corpus, ctx):
    """A/C opProbes 대표질의를 라우팅해 conformance 확인(R층)."""
    items = list(corpus["opProbes"].items())

    def one(kv):
        api, p = kv
        # B-op 은 capability-route 가 아니라 **compose(EXAONE)** 가 emit 한다 — 판정 경로가 다르다.
        #   route:"compose" 인데 --compose 가 없으면 SKIP(못 돌린 것을 통과로 위장하지 않는다).
        if p.get("route") == "compose":
            if not ctx["compose"]:
                return C(api, "SKIP", "--compose 미지정(B-op compose 경로)", query=p["probeQuery"],
                         axis={"op": api}, layer="R")
            # ⚠ **한 문장 실패 = 능력 없음이 아니다**(2026-08-01 실증: 미도달 6종 중 5종이 다른
            #   표현으로 곧바로 도달했다). 변형을 순차로 시도하고 **전부 실패해야** 미도달로 적는다.
            #   몇 번째 문장에서 도달했는지는 note 에 남긴다 — 1번이 아니면 그 표현이 취약하다는 신호.
            queries = [p["probeQuery"]] + list(p.get("probeQueryVariants") or [])
            st = note = reason = None; ev = {}
            for idx, q in enumerate(queries):
                st, note, reason, ev = _judge_compose(q, p.get("expectAny", []),
                                                      p.get("refuseOk", False), ctx["studio"],
                                                      ctx.get("compose_timeout", ctx["timeout"]))
                if st in ("PASS", "UNKNOWN"):
                    if st == "PASS" and idx > 0:
                        note = f"{note} (변형 {idx+1}번째로 도달 — 1번 문장은 취약)"
                        ev = {**ev, "variantIndex": idx, "fragileQuery": queries[0]}
                    break
            if st == "FAIL" and len(queries) > 1:
                note = f"{note} — 변형 {len(queries)}개 전부 미도달"
        else:
            st, note, reason, ev = _judge_cap(p["probeQuery"], p.get("expectAny", []),
                                              p.get("refuseOk", False), ctx["gw"], ctx["timeout"])
        return C(api, st, note, query=p["probeQuery"], reason=reason, evidence=ev,
                 axis={"op": api}, layer="R")
    return _pmap(one, items, ctx["jobs"])


def suite_capability(corpus, ctx):
    items = list(corpus["capabilityProbes"].items())

    def one(kv):
        ex, p = kv
        st, note, reason, ev = _judge_cap(p["probeQuery"], p.get("expectAny", []),
                                          p.get("refuseOk", False), ctx["gw"], ctx["timeout"])
        return C(ex, st, note, query=p["probeQuery"], reason=reason, evidence=ev,
                 axis={"executor": ex}, layer="R")
    return _pmap(one, items, ctx["jobs"])


def suite_refuse(corpus, ctx):
    def one(r):
        resp = _post(f"{ctx['gw']}/v1/capability-route", {"query": r["query"]}, ctx["timeout"])
        if _unreachable(resp):
            return C(r["id"], "UNKNOWN", "gateway 미응답", query=r["query"],
                     reason="SERVICE_DOWN", layer="R")
        refuse = resp.get("refuse", False)
        ops = resp.get("ops", [])
        # off-domain → refuse 또는 ops empty 가 정답(오라우팅 = FAIL)
        if refuse or not ops:
            return C(r["id"], "PASS", "refuse/empty=OK", query=r["query"],
                     reason="ESCALATE_BY_DESIGN", layer="R")
        got = [op.get("api", "") for op in ops]
        return C(r["id"], "FAIL", f"오라우팅 {got}", query=r["query"],
                 reason="MISROUTED", evidence={"ops": got}, layer="R")
    return _pmap(one, corpus["refuseProbes"], ctx["jobs"])


# ── combo (G층) ──────────────────────────────────────────────────────────────
def _combo_full_from_matrix(ctx):
    """be-3d 커버리지 매트릭스 **단일 콜**로 region×metric 전수(510셀)를 읽는다.

    개별 choropleth 호출(셀당 수 MB)로는 전수 스윕이 불가능하다 — 그래서 be-3d 에
    `/api/v1/metric/coverage/matrix` 를 두었다(PR #434). 여기서는 그 결과를 원장 셀로 옮긴다.
    """
    url = f"{ctx['be3d']}/api/v1/metric/coverage/matrix?regions=front"
    code, d = _get_json(url, max(ctx["timeout"], 60))
    if code != 200:
        return [C("coverage-matrix", "UNKNOWN" if code == 0 else "FAIL",
                  f"be-3d coverage matrix HTTP {code}", reason="SERVICE_DOWN" if code == 0 else "HTTP_ERROR",
                  layer="G")]
    # 지표 표시명 — GREEN 셀의 **시연 안전 질의**를 만들기 위해서다(원장 greenList → 런타임 대안 제시).
    _c, cat = _get_json(f"{ctx['be3d']}/api/v1/metric/catalog", ctx["timeout"], retries=1)
    disp = {m.get("metric_key"): (m.get("display_name") or m.get("metric_key"))
            for m in (cat.get("metrics") or [])} if _c == 200 else {}
    rows = []
    for cell in d.get("cells", []):
        led, reason = COVERAGE_STATUS.get(cell.get("status", ""), ("UNKNOWN", "UNCLASSIFIED"))
        st = {"GREEN": "PASS", "AMBER": "WARN", "RED": "FAIL", "UNKNOWN": "UNKNOWN"}[led]
        # no_data 는 '정직 갭'이며 회귀가 아니다 — FAIL 로 세지 않고 WARN 으로 표면화하되
        #   원장 상태는 RED(제안 금지)로 남긴다. 총계 FAIL 은 '깨진 것'만 세야 하기 때문.
        display = "WARN" if led == "RED" else st
        label = cell.get("region_label") or cell["region"]
        rows.append(C(f"{cell['region']}/{cell['metric']}", display,
                      f"{cell['status']} n={cell.get('with_value')} "
                      f"({round((cell.get('coverage_ratio') or 0) * 100, 1)}%)",
                      query=f"{label} {disp.get(cell['metric'], cell['metric'])} 지도로 보여줘",
                      axis={"region": cell["region"], "metric": cell["metric"],
                            "regionLabel": cell.get("region_label")},
                      reason=reason,
                      evidence={"withValue": cell.get("with_value"),
                                "measured": cell.get("measured"),
                                "estimate": cell.get("estimate"),
                                "coverageRatio": cell.get("coverage_ratio"),
                                "coverageStatus": cell.get("status"),
                                "stale": cell.get("stale")},
                      layer="G"))
        rows[-1]["_ledger"] = led
    for miss in d.get("missing", []):
        rows.append(C(f"{miss['region']}/{miss['metric']}", "UNKNOWN",
                      "캐시 미계산(무지 — '없음'이 아님)",
                      axis=miss, reason="NOT_PROBED", layer="G"))
    return rows


def _combo_render_crosscheck(ctx, green_cells, sample=3):
    """GREEN 셀 표본을 studio 렌더 경로로 재확인(G↔E 교차) — DB 는 있는데 화면이 비는 경우 탐지."""
    rows = []
    for cell in green_cells[:sample]:
        ax = cell["axis"]
        q = f"region={ax['region']}&metric={ax['metric']}&max_features=50000"
        code, d = _get_json(f"{ctx['studio']}/api/choropleth?{q}", ctx["timeout"], retries=2)
        feats = len(d.get("features", [])) if code == 200 else 0
        if code == 0:
            st, note, reason = "UNKNOWN", "studio 미응답", "SERVICE_DOWN"
        elif code == 200 and (feats > 0 or d.get("agg") == "grid"):
            st, note, reason = "PASS", f"렌더 {feats}건 일치", None
        elif code == 200:
            st, note, reason = "FAIL", "DB 는 있는데 렌더 0건", "NO_RENDERER"
        else:
            st, note, reason = "FAIL", f"HTTP {code}", "HTTP_ERROR"
        rows.append(C(f"render:{ax['region']}/{ax['metric']}", st, note, axis=ax,
                      reason=reason, evidence={"features": feats, "http": code}, layer="E"))
    return rows


def suite_combo(corpus, ctx):
    """데이터 완전성(G) — sweep 등급에 따라 범위가 달라진다(절차서 §7).

    smoke : fixtures 대표 조합 상한 12 (커밋마다)
    rep   : fixtures 대표 지역 × 전 지표 + 정책 조합
    full  : **전 지역 × 전 지표(510셀)** — be-3d coverage matrix 단일 콜 + 렌더 교차 표본
    """
    from urllib.parse import quote as _q  # noqa: F401  (기존 호환)
    fx = corpus["fixtures"]
    dims = fx["dimensions"]
    regions = fx["regions"]
    metrics = corpus["metrics"]
    buildings = [b for b in fx["buildings"] if "|" in b.get("archetype", "")]
    setpoints = dims["setpoints"]
    climates = dims["climates"]
    sweep = ctx.get("sweep", "smoke")
    rows: list[dict] = []

    # ── G층: region×metric ────────────────────────────────────────────────
    if sweep == "full":
        rows += _combo_full_from_matrix(ctx)
        greens = [r for r in rows if r.get("_ledger") == "GREEN"]
        rows += _combo_render_crosscheck(ctx, greens, sample=ctx.get("render_sample", 3))
    else:
        # ⚠ 셀 id 는 sweep 등급과 무관하게 `{region}/{metric}` 으로 고정한다.
        #   등급마다 다른 id 를 쓰면 원장에서 같은 능력이 다른 셀로 쌓여 회귀 판정이 무의미해진다.
        cases = []
        for m in metrics:                                    # metric 커버리지(강남 고정)
            cases.append(("map", f"11680/{m}", {"region": "11680", "metric": m}))
        for r in regions:                                    # region 커버리지(eui 고정)
            cases.append(("map", f"{r['id']}/eui", {"region": r["id"], "metric": "eui"}))
        limit = ctx.get("combo_limit", 12) if sweep == "smoke" else 0
        if limit:
            cases = cases[:limit]
        for _kind, label, p in cases:
            q = f"region={p['region']}&metric={p['metric']}&max_features=50000"
            code, d = _get_json(f"{ctx['studio']}/api/choropleth?{q}", ctx["timeout"], retries=2)
            ax = {"region": p["region"], "metric": p["metric"]}
            if code == 0:
                rows.append(C(label, "UNKNOWN", "studio 미응답", axis=ax,
                              reason="SERVICE_DOWN", layer="G")); continue
            if code == 429:
                rows.append(C(label, "UNKNOWN", "429 rate-limit", axis=ax,
                              reason="RATE_LIMIT", layer="G")); continue
            feats = len(d.get("features", [])) if code == 200 else 0
            honesty = d.get("honesty", "")
            if code == 200 and d.get("agg") == "grid":
                bc = d.get("building_count", 0)
                if feats and isinstance(bc, int) and bc >= feats:
                    rows.append(C(label, "PASS", f"격자 {feats}셀·{bc:,}동", axis=ax,
                                  evidence={"cells": feats, "buildings": bc}, layer="G"))
                else:
                    rows.append(C(label, "FAIL", f"격자 cells={feats} bc={bc}", axis=ax,
                                  reason="PARTIAL_DATA", layer="G"))
            elif code == 200 and honesty == "no_data":
                rows.append(C(label, "WARN", f"no_data(정직) feats={feats}", axis=ax,
                              reason="NO_DATA", layer="G"))
                rows[-1]["_ledger"] = "RED"
            elif code == 200 and feats > 0:
                rows.append(C(label, "PASS", f"feats={feats} {honesty}", axis=ax,
                              evidence={"features": feats}, layer="G"))
            elif code == 200:
                rows.append(C(label, "FAIL", f"200이나 feats=0 {honesty}", axis=ax,
                              reason="NO_RENDERER", layer="G"))
            else:
                rows.append(C(label, "FAIL", f"HTTP {code} {str(d.get('error',''))[:30]}", axis=ax,
                              reason="HTTP_ERROR", layer="G"))

    # ── E층: 정책 조합(bldg × setpoint × climate) ─────────────────────────
    pcases = []
    for b in buildings:
        bt, hv = b["archetype"].split("|", 1)
        pcases.append((f"bldg:{bt}|{hv}", {"bt": bt, "hv": hv, "sp": setpoints[1], "cl": climates[0]}))
    for sp in setpoints:
        pcases.append((f"sp:{sp}", {"bt": "large_office", "hv": "A", "sp": sp, "cl": climates[0]}))
    if sweep == "smoke":
        pcases = pcases[:4]
    for label, p in pcases:
        body = {"building_type": p["bt"], "hvac_type": p["hv"], "city": "Seoul",
                "scenario": p["cl"], "setpoint": p["sp"], "ems": "M00"}
        resp = _post(f"{ctx['gw']}/v1/climate-scenario", body, ctx["timeout"])
        ax = {"buildingType": p["bt"], "hvac": p["hv"], "setpoint": p["sp"], "climate": p["cl"]}
        if _unreachable(resp):
            rows.append(C(label, "UNKNOWN", "gateway 미응답", axis=ax,
                          reason="SERVICE_DOWN", layer="E")); continue
        # HTTP 오류는 종류별로 다르게 읽는다. 429(과호출)를 '능력 없음'으로 적으면 스윕 자체가
        #   거짓 회귀를 만든다 — 실제로 2026-08-01 첫 전수에서 sp:c26h18/c26h22 가 이 경로로
        #   NO_RENDERER 오분류돼 회귀 2건이 잘못 떴다(엔드포인트는 정상이었다).
        err = resp.get("_http_error")
        if err == 404:
            rows.append(C(label, "WARN", "404 미커버(F14 폴백)", axis=ax,
                          reason="PARTIAL_DATA", layer="E")); continue
        if err == 429:
            rows.append(C(label, "UNKNOWN", "429 rate-limit", axis=ax,
                          reason="RATE_LIMIT", layer="E")); continue
        if err and err >= 500:
            rows.append(C(label, "UNKNOWN", f"HTTP {err}(서버 일시 오류)", axis=ax,
                          reason="SERVICE_DOWN", evidence={"http": err}, layer="E")); continue
        if err:
            rows.append(C(label, "FAIL", f"HTTP {err}", axis=ax,
                          reason="HTTP_ERROR", evidence={"http": err}, layer="E")); continue
        kwh = (resp.get("estimate") or {}).get("site_kwh")
        if isinstance(kwh, (int, float)) and kwh > 0:
            rows.append(C(label, "PASS", f"site_kwh={round(kwh)}", axis=ax,
                          evidence={"siteKwh": kwh}, layer="E"))
        else:
            rows.append(C(label, "FAIL", f"kwh={kwh} {str(resp)[:40]}", axis=ax,
                          reason="NO_RENDERER", layer="E"))
    return rows


def suite_scenario(corpus, ctx):
    """B-op 3D 시연 = be-3d public_scenarios 재생 표면(E층) 등록 확인."""
    rows = []
    candidates = [
        (f"{ctx['studio']}/api/v1/scenarios?limit=50", "studio-proxy"),
        (f"{ctx['be3d']}/api/v1/scenarios?limit=50", "be3d-direct"),
    ]
    listed = None
    for url, tag in candidates:
        code, d = _get_json(url, ctx["timeout"], retries=2)
        if code == 200:
            items = (d if isinstance(d, list)
                     else d.get("scenarios") or d.get("items") or d.get("results") or [])
            listed = (tag, len(items))
            rows.append(C(f"registry:{tag}", "PASS" if items else "WARN",
                          f"{len(items)} scenario 등록" if items else "등록 0(빈 목록)",
                          evidence={"count": len(items)}, layer="E"))
            break
        rows.append(C(f"registry:{tag}", "UNKNOWN" if code == 0 else "SKIP", f"HTTP {code}",
                      reason="SERVICE_DOWN" if code == 0 else None, layer="E"))
    if listed is None:
        rows.append(C("scenario-registry", "UNKNOWN",
                      "public_scenarios 미응답 — B-op 재생 표면 미검증",
                      reason="SERVICE_DOWN", layer="E"))
    return rows


def suite_static(corpus, ctx):
    """서비스 불요. gen_corpus --check(drift) + A/C 커버리지 게이트(D층)."""
    rows = []
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True)
    rows.append(C("gen-drift", "PASS" if r.returncode == 0 else "FAIL",
                  (r.stdout + r.stderr).strip().splitlines()[-1][:60] if (r.stdout or r.stderr) else "",
                  reason=None if r.returncode == 0 else "DECL_DRIFT", layer="D"))
    cov = corpus["coverage"]
    ac_missing = cov.get("acMissing", [])
    rows.append(C("ac-coverage", "PASS" if not ac_missing else "FAIL",
                  "11/11" if not ac_missing else f"미커버 {ac_missing}",
                  reason=None if not ac_missing else "NOT_PROBED", layer="D"))
    bcov = cov.get("bop", {})
    nl_total, nl_cov = bcov.get("nlTarget", 0), bcov.get("nlCovered", 0)
    nl_un = len(bcov.get("nlUncovered", []))
    exempt = len(bcov.get("lifecycleExempt", []))
    # 분모를 나눠 보고한다: 생명주기 op(clear*/unmount*)는 자연어 대표질의가 **원리적으로 불필요**.
    #   하나로 뭉뚱그린 "5/85" 는 78개가 방치된 것처럼 읽혔지만 그중 18은 면제 대상이었다.
    rows.append(C("bop-coverage", "WARN" if nl_un else "PASS",
                  f"NL대상 {nl_cov}/{nl_total} 커버 · 미커버 {nl_un} · 생명주기 면제 {exempt}",
                  reason="NOT_PROBED" if nl_un else None, layer="D"))
    return rows


SUITES = {"static": suite_static, "class": suite_class, "opcode": suite_opcode,
          "capability": suite_capability, "refuse": suite_refuse,
          "combo": suite_combo, "scenario": suite_scenario}

SUITE_SERVICES = {                       # 각 suite 가 요구하는 서비스(P0 프리플라이트)
    "static": set(), "class": {"gw", "studio"}, "opcode": {"gw"},
    "capability": {"gw"}, "refuse": {"gw"}, "combo": {"gw", "studio", "be3d"},
    "scenario": {"be3d"},
}

# git diff 파일 → 영향 suite 매핑(사용자 요구: '수정 발생 시 전수')
CHANGE_MAP = [
    ("op_registry.json", ["static", "opcode", "class", "scenario"]),
    ("router_meta.json", ["capability", "refuse", "class"]),
    ("klue_router",      ["capability", "refuse", "class"]),
    ("executor_keys",    ["static", "capability"]),
    ("query_overlay",    ["static", "class", "opcode", "capability", "combo"]),
    ("intent.ts",        ["class", "opcode", "combo"]),
    ("choropleth",       ["combo"]),
    ("metric_coverage",  ["combo"]),
    ("f14",              ["combo"]),
    ("climate",          ["combo"]),
    ("sigungu",          ["combo"]),
    ("region_camera",    ["combo", "scenario"]),
    ("metric_catalog",   ["combo"]),
    ("public_scenarios", ["scenario"]),
    ("compose",          ["class", "opcode"]),
    # 모델 스왑 = 전면
    ("run24", ["static", "class", "opcode", "capability", "refuse", "combo", "scenario"]),
]


def suites_for_changes(files: list[str]) -> list[str]:
    picked: list[str] = []
    for f in files:
        for token, suites in CHANGE_MAP:
            if token in f:
                for s in suites:
                    if s not in picked:
                        picked.append(s)
    return picked or ["static"]


# ── P0 프리플라이트(절차서 §4) ────────────────────────────────────────────────
def preflight(ctx, needed: set[str]) -> dict:
    """서비스 생존 + 버전 확인. 여기서 실패하면 이후 판정이 전부 UNKNOWN 으로 오염된다."""
    out = {}
    probes = {
        "gw":     (f"{ctx['gw']}/health/full", "gateway"),
        "studio": (f"{ctx['studio']}/api/ops-status", "studio"),
        "be3d":   (f"{ctx['be3d']}/api/v1/metric/coverage/axes", "be-3d"),
    }
    for key, (url, label) in probes.items():
        if key not in needed:
            continue
        code, body = _get_json(url, min(ctx["timeout"], 15), retries=2)
        detail = ""
        if key == "gw" and isinstance(body, dict):
            detail = str(body.get("version") or body.get("status") or "")[:20]
        elif key == "be3d" and isinstance(body, dict):
            detail = f"metric {body.get('metricCount')}·region {body.get('regionCount')}"
        elif key == "studio" and isinstance(body, dict):
            detail = str(body.get("gateway", {}).get("status", ""))[:20]
        out[key] = {"url": url, "label": label, "ok": code == 200, "http": code, "detail": detail}
    return out


# ── 능력 원장 ────────────────────────────────────────────────────────────────
def _ledger_status(cell: dict) -> str:
    return cell.get("_ledger") or LEDGER_STATUS.get(cell["status"], "UNKNOWN")


def _cell_key(cell: dict) -> str:
    return f"{cell['suite']}:{cell['id']}"


def build_ledger(corpus, cells: list[dict], services: dict, ctx, baseline: dict | None) -> dict:
    """원장 조립 — 직전본 대비 회귀 판정 + **미실행 셀 이월**.

    이월(carry-over)이 필요한 이유: `--suite combo` 처럼 일부만 돌린 결과로 원장을 덮어쓰면
    나머지 능력이 원장에서 사라진다. 사라진 것과 잃은 것은 다르다 — 직전 값을 시각과 함께
    보존하고 `carriedOver` 로 표시한다(신선도는 probedAt 으로 판단).
    """
    now = datetime.now(timezone.utc).isoformat()
    prev, prev_rows = {}, {}
    if baseline:
        for c in baseline.get("cells", []):
            k = f"{c.get('suite')}:{c.get('id')}"
            prev[k] = c.get("status")
            prev_rows[k] = c

    out_cells, summary, by_reason = [], {}, {}
    regressions, greenlist = [], []
    for c in cells:
        led = _ledger_status(c)
        key = _cell_key(c)
        prev_st = prev.get(key)
        row = {"suite": c["suite"], "id": c["id"], "layer": c.get("layer"),
               "status": led, "verdict": c["status"], "reason": c.get("reason"),
               "note": c.get("note"), "axis": c.get("axis") or {},
               "query": c.get("query"), "evidence": c.get("evidence") or {},
               "prevStatus": prev_st, "probedAt": now, "carriedOver": False}
        out_cells.append(row)
        summary[led] = summary.get(led, 0) + 1
        if c.get("reason"):
            by_reason[c["reason"]] = by_reason.get(c["reason"], 0) + 1
        # 회귀 = '잃어버린 능력'만(총계 아님). UNKNOWN 은 회귀로 세지 않는다(§1.3).
        if prev_st == "GREEN" and led in ("RED",):
            regressions.append({"key": key, "from": prev_st, "to": led,
                                "reason": c.get("reason"), "axis": c.get("axis")})
        if led == "GREEN" and c.get("query"):
            # verifiedBy 를 반드시 남긴다: router = 실제로 자연어→op 라우팅까지 확인된 질의,
            #   data = 데이터 존재만 확인(문장은 합성). 둘을 섞으면 "된다고 했는데 못 알아듣는" 사고.
            greenlist.append({"query": c["query"], "suite": c["suite"], "id": c["id"],
                              "layer": c.get("layer"), "axis": c.get("axis") or {},
                              "verifiedBy": "router" if c.get("layer") == "R" else "data"})

    fresh_keys = {f"{r['suite']}:{r['id']}" for r in out_cells}
    fresh_count = len(out_cells)
    carried = 0
    for k, row in prev_rows.items():                 # 이번에 안 돌린 셀 이월(값·시각 보존)
        if k in fresh_keys:
            continue
        r = dict(row)
        r["carriedOver"] = True
        r.setdefault("probedAt", baseline.get("generatedAt") if baseline else None)
        out_cells.append(r)
        summary[r.get("status", "UNKNOWN")] = summary.get(r.get("status", "UNKNOWN"), 0) + 1
        carried += 1
        if r.get("status") == "GREEN" and r.get("query"):
            greenlist.append({"query": r["query"], "suite": r.get("suite"), "id": r.get("id"),
                              "layer": r.get("layer"), "axis": r.get("axis") or {},
                              "verifiedBy": "router" if r.get("layer") == "R" else "data",
                              "stale": True})

    total = len(out_cells)
    # 무효 판정(§1.3)은 **이번에 실제로 돈 셀**로만 계산한다 — 이월된 옛 UNKNOWN 이 스윕을 무효로
    #   만들면 영원히 회복 못 한다.
    unknown = sum(1 for c in cells if _ledger_status(c) == "UNKNOWN")
    return {
        "schemaVersion": "1.0",
        "generatedAt": now,
        "sweep": ctx.get("sweep"),
        "suitesRun": sorted({c["suite"] for c in cells}),
        "corpusCounts": corpus.get("counts", {}),
        "services": services,
        "cells": out_cells,
        "summary": {**summary, "total": total, "fresh": fresh_count, "carriedOver": carried,
                    "unknownRatio": round(unknown / fresh_count, 4) if fresh_count else 0.0},
        "byReason": by_reason,
        "greenList": greenlist,
        "regressions": regressions,
        "honesty": ("UNKNOWN = 판정 실패(서비스 다운·미계산)이며 '능력 없음'이 아니다. "
                    "RED = 실측 결과 불가. 회귀 판정은 총계가 아니라 GREEN→RED 만 센다."),
    }


def print_ledger_summary(ledger: dict) -> None:
    s = ledger["summary"]
    print("\n" + "=" * 74)
    print(f"  능력 원장 — GREEN {s.get('GREEN',0)} / AMBER {s.get('AMBER',0)} / "
          f"RED {s.get('RED',0)} / UNKNOWN {s.get('UNKNOWN',0)} / SKIP {s.get('SKIP',0)}"
          f"  (셀 {s['total']} = 이번 {s.get('fresh', s['total'])} + 이월 {s.get('carriedOver', 0)})")
    if ledger["byReason"]:
        top = sorted(ledger["byReason"].items(), key=lambda kv: -kv[1])[:6]
        print("  사유: " + ", ".join(f"{k}={v}" for k, v in top))
    print(f"  시연 가능 질의(greenList): {len(ledger['greenList'])}건")
    if ledger["regressions"]:
        print(f"  ❌ 능력 회귀 {len(ledger['regressions'])}건 — 잃어버린 능력:")
        for r in ledger["regressions"][:10]:
            print(f"     · {r['key']}  {r['from']}→{r['to']}  ({r['reason']})")
    else:
        print("  ✅ 회귀(GREEN→RED) 0건")
    print("=" * 74)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--suite", nargs="+", choices=list(SUITES))
    ap.add_argument("--changed", nargs="+", metavar="FILE")
    ap.add_argument("--compose", action="store_true", help="compose 경로 라이브(느림)")
    ap.add_argument("--sweep", choices=["smoke", "rep", "full"], default="smoke",
                    help="G층 범위: smoke(대표 12) / rep(대표지역×전지표) / full(전지역×전지표 510셀)")
    ap.add_argument("--combo-limit", type=int, default=12, help="smoke 시 combo 상한(0=전부)")
    ap.add_argument("--render-sample", type=int, default=3, help="full 시 렌더 교차확인 표본 수")
    ap.add_argument("--jobs", type=int, default=4, help="라우팅 프로브 병렬도")
    ap.add_argument("--report", nargs="?", const=str(LEDGER_JSON), default=None,
                    metavar="PATH", help="능력 원장 JSON 산출(기본 corpus/capability_ledger.json)")
    ap.add_argument("--baseline", nargs="?", const=str(LEDGER_JSON), default=None,
                    metavar="PATH", help="직전 원장과 비교해 회귀(GREEN→RED) 판정")
    ap.add_argument("--allow-degraded", action="store_true",
                    help="프리플라이트 실패해도 진행(원장은 쓰지 않음)")
    ap.add_argument("--gateway", default=DEFAULT_GATEWAY)
    ap.add_argument("--studio", default=DEFAULT_STUDIO)
    ap.add_argument("--be3d", default=DEFAULT_BE3D)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--compose-timeout", type=int, default=150,
                    help="compose(EXAONE 생성) 경로 타임아웃 — 라우팅(30s)보다 훨씬 길다. "
                         "짧게 두면 느린 성공이 UNKNOWN 으로 잡혀 스윕이 통째로 무효가 된다(2026-08-01 실증)")
    args = ap.parse_args()

    if not CORPUS_JSON.exists():
        print("❌ query_corpus.generated.json 부재 → python corpus/gen_corpus.py 먼저"); sys.exit(1)
    corpus = json.loads(CORPUS_JSON.read_text(encoding="utf-8"))

    if args.all:
        run = ["static", "opcode", "capability", "class", "refuse", "combo", "scenario"]
    elif args.changed:
        run = suites_for_changes(args.changed)
        print(f"[changed] {args.changed} → suite: {run}")
    elif args.suite:
        run = args.suite
    else:
        run = ["static"]

    ctx = {"gw": args.gateway, "studio": args.studio, "be3d": args.be3d,
           "timeout": args.timeout, "compose": args.compose, "combo_limit": args.combo_limit,
           "sweep": args.sweep, "jobs": max(1, args.jobs), "render_sample": args.render_sample,
           "compose_timeout": args.compose_timeout}
    c = corpus["counts"]
    print("=" * 74)
    print(f"  질의 코퍼스 전수 — opcode {c['opcodes']}(A{c['opA']}/B{c['opB']}/C{c['opC']}) "
          f"router {c['routerClasses']} executor {c['executors']} queryClass {c['queryClasses']}")
    print(f"  suites={run}  sweep={args.sweep}  jobs={ctx['jobs']}")
    print(f"  gateway={args.gateway}  studio={args.studio}  be3d={args.be3d}")
    print("=" * 74)

    # ── P0 프리플라이트 ───────────────────────────────────────────────────
    needed = set().union(*[SUITE_SERVICES[s] for s in run]) if run else set()
    services = preflight(ctx, needed) if needed else {}
    degraded = [k for k, v in services.items() if not v["ok"]]
    for k, v in services.items():
        print(f"  {'✅' if v['ok'] else '❌'} preflight {v['label']:8s} HTTP {v['http']} {v['detail']}")
    if degraded and not args.allow_degraded:
        print(f"\n❌ 프리플라이트 실패({', '.join(degraded)}) — 스윕 중단.")
        print("   서비스 다운을 능력 부재로 오독하지 않기 위해 진행하지 않는다(절차서 §1.3).")
        print("   그래도 돌리려면 --allow-degraded (원장은 기록하지 않음).")
        sys.exit(2)

    grand = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0, "UNKNOWN": 0}
    all_cells: list[dict] = []
    for name in run:
        t0 = time.time()
        rows = [_normalize(r) for r in SUITES[name](corpus, ctx)]
        for r in rows:
            r["suite"] = name
        all_cells += rows
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0, "UNKNOWN": 0}
        print(f"\n── suite:{name} ({len(rows)} 케이스) ──")
        preview = rows if len(rows) <= 40 else rows[:20]
        for r in rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            grand[r["status"]] = grand.get(r["status"], 0) + 1
        for r in preview:
            print(f"  {ICON.get(r['status'],'?')} {str(r['id']):<26} {str(r['note'])[:44]}")
        if len(rows) > 40:
            print(f"  … {len(rows)-20}건 생략(전체는 --report 원장 참조)")
        print(f"  → PASS {counts['PASS']} WARN {counts['WARN']} FAIL {counts['FAIL']} "
              f"SKIP {counts['SKIP']} UNKNOWN {counts['UNKNOWN']}  ({time.time()-t0:.1f}s)")

    total = sum(grand.values())
    print("\n" + "=" * 74)
    print(f"총계: PASS {grand['PASS']}/{total}  WARN {grand['WARN']}  FAIL {grand['FAIL']}  "
          f"SKIP {grand['SKIP']}  UNKNOWN {grand['UNKNOWN']}")
    print("=" * 74)

    # ── 원장 산출 + 회귀 판정 ─────────────────────────────────────────────
    baseline, prior_path = None, None
    # 비교·이월 기준: --baseline 이 있으면 그것, 없으면 기록할 원장 파일의 직전본.
    if args.baseline and Path(args.baseline).exists():
        prior_path = Path(args.baseline)
    elif args.report and Path(args.report).exists():
        prior_path = Path(args.report)
    if prior_path:
        try:
            baseline = json.loads(prior_path.read_text(encoding="utf-8"))
            print(f"[baseline] {prior_path.name} — 셀 {len(baseline.get('cells', []))} "
                  f"({baseline.get('generatedAt','')[:19]})")
        except Exception as e:
            print(f"⚠️ baseline 로드 실패({e}) — 회귀 판정·이월 생략")
    ledger = build_ledger(corpus, all_cells, services, ctx, baseline)
    unknown_ratio = ledger["summary"]["unknownRatio"]

    if args.report or args.baseline:
        print_ledger_summary(ledger)

    invalid = unknown_ratio > UNKNOWN_ABORT_RATIO
    if invalid:
        print(f"\n⚠️ UNKNOWN 비율 {unknown_ratio:.1%} > {UNKNOWN_ABORT_RATIO:.0%} — "
              f"스윕 무효(원장 미기록). 서비스 상태 확인 후 재실행.")
    elif args.report and not degraded:
        Path(args.report).write_text(json.dumps(ledger, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
        print(f"\n📒 능력 원장 기록: {args.report}  (셀 {ledger['summary']['total']})")

    if invalid:
        sys.exit(2)
    sys.exit(1 if (grand["FAIL"] or ledger["regressions"]) else 0)


if __name__ == "__main__":
    main()
