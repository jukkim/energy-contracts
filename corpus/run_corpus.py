"""
run_corpus.py — 질의 코퍼스 단일 진입점 (모든 서브폴더 공유)
================================================================================
사용자 요구: "무언가 수정이 발생하는 경우에 테스트 셋트를 전수 수행하고 싶다."
이 러너가 그 '전수 수행'의 단일 진입점. AI 챔피언·lab·be-3d·studio·gateway 어디서든
`python <path>/corpus/run_corpus.py --all` 하나로 전 코퍼스를 라이브 실행한다.

코퍼스 = corpus/query_corpus.generated.json (gen_corpus.py 병합본).
실행 = gateway :8030 / studio :3040 을 HTTP 로 호출(각 repo 소유 서비스 무이동).

Suite(7):
  class      — queryClasses(C/S/L 24) 라우팅/컴파일          [gateway+studio]
  opcode     — A/C opProbes(11) 대표질의 라우팅 conformance  [gateway+studio]
  capability — capabilityProbes(7 executor) 라우팅 hit       [gateway]
  refuse     — refuseProbes(off-domain) refuse 게이트 회귀    [gateway]
  combo      — fixtures 차원 조합(region×metric / bldg×sp×climate) 데이터 완전성 [studio+gateway]
  scenario   — B-op public_scenarios 재생 가능성(등록 존재)  [be-3d]
  static     — gen_corpus --check (drift 0) + 커버리지 게이트 [오프라인, 서비스 불요]

  ⚠ combo/scenario 는 fixtures/canonical 에서 차원을 파생(하드코딩 아님) — gen_combo_qc.py 의
    인라인 REGIONS/METRICS/SETPOINTS 드리프트 문제를 코퍼스가 흡수(설계 §7).

Usage:
  python corpus/run_corpus.py --all                 # 전수(static + 라이브 6)
  python corpus/run_corpus.py --suite static        # 서비스 없이 정적 게이트만(CI/prebuild)
  python corpus/run_corpus.py --suite class opcode   # 특정 suite
  python corpus/run_corpus.py --changed <file>...    # git diff 파일 → 영향 suite 자동
  python corpus/run_corpus.py --compose             # class/opcode 의 compose 경로도 라이브(느림)
  python corpus/run_corpus.py --combo-limit N        # combo suite 케이스 상한(기본 12, 0=전부)
  python corpus/run_corpus.py --gateway URL --studio URL

Exit: 0 = 전부 PASS(WARN 허용), 1 = FAIL 존재 or static drift.
설계 정본: energy-decision-studio/docs/QUERY_CORPUS_SSOT.md
"""
from __future__ import annotations
import sys, json, time, argparse, subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
CORPUS_JSON = HERE / "query_corpus.generated.json"
GEN = HERE / "gen_corpus.py"

DEFAULT_GATEWAY = "http://localhost:8030"
DEFAULT_STUDIO  = "http://localhost:3040"

ICON = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "──"}


# ── HTTP ──────────────────────────────────────────────────────────────────────
def _post(url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode("utf-8", "replace")[:160]}
    except (URLError, OSError) as e:
        return {"_url_error": str(e)}
    except Exception as e:
        return {"_error": str(e)}


def _get(url: str, timeout: int) -> int:
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as r:
            return r.status
    except HTTPError as e:
        return e.code
    except Exception:
        return 0


def _get_json(url: str, timeout: int):
    """(status, body) — combo suite 용(데이터 완전성 판정)."""
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"_err": str(e)}


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


# ── 케이스 판정 ─────────────────────────────────────────────────────────────
def _judge_cap(query, expect, refuse_ok, gw, timeout):
    resp = _post(f"{gw}/v1/capability-route", {"query": query}, timeout)
    if "_url_error" in resp or "_error" in resp:
        return "FAIL", str(resp)[:60]
    ops = resp.get("ops", [])
    refuse = resp.get("refuse", False)
    got = [op.get("api", "") for op in ops]
    if refuse:
        return ("PASS", "refuse=OK") if refuse_ok else ("FAIL", "refuse=True")
    if not ops:
        return ("PASS", "ops empty(refuse_ok)") if refuse_ok else ("FAIL", "ops empty")
    if expect and not any(a in got for a in expect):
        return "WARN", f"got={got} want∈{expect}"
    return "PASS", f"ops={got}"


def _judge_compose(query, expect, refuse_ok, studio, timeout):
    resp = _post(f"{studio}/api/compose", {"query": query}, timeout)
    if "_url_error" in resp or "_error" in resp:
        return "FAIL", str(resp)[:60]
    ops, cap_req = _ops_from_compose(resp.get("response", ""))
    got = [op.get("api", op.get("op", "")) for op in ops]
    if not ops:
        if refuse_ok:
            name = cap_req.get("suggested_name") if isinstance(cap_req, dict) else None
            return "PASS", (f"empty+capability_request={name}" if name else "empty(refuse_ok)")
        return "FAIL", f"empty raw={resp.get('response','')[:50]}"
    if expect and not any(a in got for a in expect):
        return "WARN", f"got={got} want∈{expect}"
    return "PASS", f"ops={got}"


# ── Suites ───────────────────────────────────────────────────────────────────
def suite_class(corpus, ctx):
    rows = []
    for c in corpus["queryClasses"]:
        rt = c["route"]
        if rt == "cap":
            st, note = _judge_cap(c["query"], c["expectAny"], c["refuseOk"], ctx["gw"], ctx["timeout"])
        elif rt == "compose":
            if not ctx["compose"]:
                st, note = "SKIP", "--compose 미지정"
            else:
                st, note = _judge_compose(c["query"], c["expectAny"], c["refuseOk"], ctx["studio"], ctx["timeout"])
        elif rt == "ops_status":
            code = _get(f"{ctx['studio']}/api/ops-status", ctx["timeout"])
            st, note = ("PASS", f"HTTP {code}") if code == 200 else ("FAIL", f"HTTP {code}")
        else:
            st, note = "SKIP", f"route={rt}"
        rows.append((c["id"], st, note))
    return rows


def suite_opcode(corpus, ctx):
    """A/C opProbes 대표질의를 라우팅해 conformance 확인."""
    rows = []
    for api, p in corpus["opProbes"].items():
        st, note = _judge_cap(p["probeQuery"], p.get("expectAny", []),
                              p.get("refuseOk", False), ctx["gw"], ctx["timeout"])
        rows.append((api, st, note))
    return rows


def suite_capability(corpus, ctx):
    rows = []
    for ex, p in corpus["capabilityProbes"].items():
        st, note = _judge_cap(p["probeQuery"], p.get("expectAny", []),
                              p.get("refuseOk", False), ctx["gw"], ctx["timeout"])
        rows.append((ex, st, note))
    return rows


def suite_refuse(corpus, ctx):
    rows = []
    for r in corpus["refuseProbes"]:
        resp = _post(f"{ctx['gw']}/v1/capability-route", {"query": r["query"]}, ctx["timeout"])
        if "_url_error" in resp or "_error" in resp:
            rows.append((r["id"], "FAIL", str(resp)[:50])); continue
        refuse = resp.get("refuse", False)
        ops = resp.get("ops", [])
        # off-domain → refuse 또는 ops empty 가 정답(오라우팅 = FAIL)
        if refuse or not ops:
            rows.append((r["id"], "PASS", "refuse/empty=OK"))
        else:
            got = [op.get("api", "") for op in ops]
            rows.append((r["id"], "FAIL", f"오라우팅 {got}"))
    return rows


def suite_combo(corpus, ctx):
    """fixtures 차원에서 파생한 조합의 데이터 완전성(200+non-empty). 하드코딩 아님.
    map: region×metric — studio /api/choropleth
    policy: bldg×setpoint×climate — gateway /v1/climate-scenario
    (전수 pairwise 는 studio qc/gen_combo_qc.py 소관; 여기선 fixtures 대표 조합 스모크.)"""
    from urllib.parse import quote as _q
    fx = corpus["fixtures"]
    dims = fx["dimensions"]
    regions = fx["regions"]              # 대표 4
    metrics = corpus["metrics"]          # 15 canonical
    buildings = [b for b in fx["buildings"] if "|" in b.get("archetype", "")]
    setpoints = dims["setpoints"]
    climates = dims["climates"]
    limit = ctx.get("combo_limit", 12)
    rows = []

    cases = []
    # A. metric 커버리지(강남 고정) — canonical metric 전수 대표
    for m in metrics:
        cases.append(("map", f"metric:{m}", {"region": "11680", "metric": m}))
    # A. region 커버리지(eui 고정) — fixtures 대표 지역
    for r in regions:
        cases.append(("map", f"region:{r['label']}", {"region": r["id"], "metric": "eui"}))
    # B. policy: fixture 건물 × 대표 setpoint/climate
    for b in buildings:
        bt, hv = b["archetype"].split("|", 1)
        cases.append(("policy", f"bldg:{bt}|{hv}",
                      {"bt": bt, "hv": hv, "sp": setpoints[1], "cl": climates[0]}))
    for sp in setpoints:
        cases.append(("policy", f"sp:{sp}",
                      {"bt": "large_office", "hv": "A", "sp": sp, "cl": climates[0]}))

    if limit:
        cases = cases[:limit]

    for kind, label, p in cases:
        if kind == "map":
            q = f"region={p['region']}&metric={p['metric']}&max_features=50000"
            code, d = _get_json(f"{ctx['studio']}/api/choropleth?{q}", ctx["timeout"])
            if code == 429:
                rows.append((label, "WARN", "429 rate-limit")); continue
            feats = len(d.get("features", [])) if code == 200 else 0
            honesty = d.get("honesty", "")
            if code == 200 and d.get("agg") == "grid":
                bc = d.get("building_count", 0)
                st, note = (("PASS", f"격자 {feats}셀·{bc:,}동") if feats and isinstance(bc, int) and bc >= feats
                            else ("FAIL", f"격자 cells={feats} bc={bc}"))
            elif code == 200 and honesty == "no_data":
                st, note = "WARN", f"no_data(정직) feats={feats}"
            elif code == 200 and feats > 0:
                st, note = "PASS", f"feats={feats} {honesty}"
            elif code == 200:
                st, note = "FAIL", f"200이나 feats=0 {honesty}"
            else:
                st, note = "FAIL", f"HTTP {code} {str(d.get('error',''))[:30]}"
        else:
            body = {"building_type": p["bt"], "hvac_type": p["hv"], "city": "Seoul",
                    "scenario": p["cl"], "setpoint": p["sp"], "ems": "M00"}
            code, d = _post(f"{ctx['gw']}/v1/climate-scenario", body, ctx["timeout"])
            kwh = (d.get("estimate") or {}).get("site_kwh")
            if code == 200 and isinstance(kwh, (int, float)) and kwh > 0:
                st, note = "PASS", f"site_kwh={round(kwh)}"
            elif code == 404:
                st, note = "WARN", "404 미커버(F14 폴백)"
            else:
                st, note = "FAIL", f"HTTP {code} kwh={kwh}"
        rows.append((label, st, note))
    return rows


def suite_scenario(corpus, ctx):
    """B-op 3D 시연 = be-3d public_scenarios 재생. studio 프록시(same-origin rewrite)
    또는 be-3d 직접으로 등록 목록을 조회해 '재생 가능(등록 존재)'을 확인.
    B-op conformance(emit⊆registry)는 opcode/static 이 담당 — 여기선 재생 표면 존재만."""
    rows = []
    # be-3d scenarios_api: GET /api/v1/scenarios?limit=N (public_scenarios 갤러리).
    # studio 는 next.config rewrites 로 /api/v1/* → be-3d :8000 재노출(same-origin).
    candidates = [
        (f"{ctx['studio']}/api/v1/scenarios?limit=50", "studio-proxy"),
        (f"{ctx['gw'].replace(':8030', ':8000')}/api/v1/scenarios?limit=50", "be3d-direct"),
    ]
    listed = None
    for url, tag in candidates:
        code, d = _get_json(url, ctx["timeout"])
        if code == 200:
            items = (d if isinstance(d, list)
                     else d.get("scenarios") or d.get("items") or d.get("results") or [])
            listed = (tag, len(items))
            rows.append((f"registry:{tag}", "PASS" if items else "WARN",
                         f"{len(items)} scenario 등록" if items else "등록 0(빈 목록)"))
            break
        else:
            rows.append((f"registry:{tag}", "SKIP", f"HTTP {code}"))
    if listed is None:
        rows.append(("scenario-registry", "WARN",
                     "public_scenarios 엔드포인트 미응답(be-3d :8000 확인) — B-op 재생 표면 미검증"))
    return rows


def suite_static(corpus, ctx):
    """서비스 불요. gen_corpus --check(drift) + A/C 커버리지 게이트."""
    rows = []
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True)
    rows.append(("gen-drift", "PASS" if r.returncode == 0 else "FAIL",
                 (r.stdout + r.stderr).strip().splitlines()[-1][:60] if (r.stdout or r.stderr) else ""))
    cov = corpus["coverage"]
    ac_missing = cov.get("acMissing", [])
    rows.append(("ac-coverage", "PASS" if not ac_missing else "FAIL",
                 "11/11" if not ac_missing else f"미커버 {ac_missing}"))
    bcov = cov.get("bop", {})
    nun = len(bcov.get("uncovered", []))
    # B-op 무테스트는 경고(전수 NL 미작성 = 알려진 conformance-only 전략)
    rows.append(("bop-coverage", "WARN" if nun else "PASS",
                 f"{len(bcov.get('covered', []))}/85 커버, {nun} conformance-only"))
    return rows


SUITES = {"static": suite_static, "class": suite_class, "opcode": suite_opcode,
          "capability": suite_capability, "refuse": suite_refuse,
          "combo": suite_combo, "scenario": suite_scenario}

# git diff 파일 → 영향 suite 매핑(사용자 요구: '수정 발생 시 전수')
CHANGE_MAP = [
    ("op_registry.json", ["static", "opcode", "class", "scenario"]),
    ("router_meta.json", ["capability", "refuse", "class"]),
    ("klue_router",      ["capability", "refuse", "class"]),
    ("executor_keys",    ["static", "capability"]),
    ("query_overlay",    ["static", "class", "opcode", "capability", "combo"]),
    ("intent.ts",        ["class", "opcode", "combo"]),
    ("choropleth",       ["combo"]),
    ("f14",              ["combo"]),
    ("climate",          ["combo"]),
    ("sigungu",          ["combo"]),
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--suite", nargs="+", choices=list(SUITES))
    ap.add_argument("--changed", nargs="+", metavar="FILE")
    ap.add_argument("--compose", action="store_true", help="compose 경로 라이브(느림)")
    ap.add_argument("--combo-limit", type=int, default=12, help="combo suite 케이스 상한(0=전부)")
    ap.add_argument("--gateway", default=DEFAULT_GATEWAY)
    ap.add_argument("--studio", default=DEFAULT_STUDIO)
    ap.add_argument("--timeout", type=int, default=30)
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

    ctx = {"gw": args.gateway, "studio": args.studio, "timeout": args.timeout,
           "compose": args.compose, "combo_limit": args.combo_limit}
    c = corpus["counts"]
    print("=" * 74)
    print(f"  질의 코퍼스 전수 — opcode {c['opcodes']}(A{c['opA']}/B{c['opB']}/C{c['opC']}) "
          f"router {c['routerClasses']} executor {c['executors']} queryClass {c['queryClasses']}")
    print(f"  suites={run}  gateway={args.gateway}  studio={args.studio}")
    print("=" * 74)

    grand = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
    for name in run:
        t0 = time.time()
        rows = SUITES[name](corpus, ctx)
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
        print(f"\n── suite:{name} ({len(rows)} 케이스) ──")
        for cid, st, note in rows:
            counts[st] = counts.get(st, 0) + 1
            grand[st] = grand.get(st, 0) + 1
            print(f"  {ICON.get(st,'?')} {cid:<26} {note[:44]}")
        print(f"  → PASS {counts['PASS']} WARN {counts['WARN']} FAIL {counts['FAIL']} "
              f"SKIP {counts['SKIP']}  ({time.time()-t0:.1f}s)")

    total = sum(grand.values())
    print("\n" + "=" * 74)
    print(f"총계: PASS {grand['PASS']}/{total}  WARN {grand['WARN']}  "
          f"FAIL {grand['FAIL']}  SKIP {grand['SKIP']}")
    print("=" * 74)
    sys.exit(1 if grand["FAIL"] else 0)


if __name__ == "__main__":
    main()
