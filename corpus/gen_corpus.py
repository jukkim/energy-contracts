"""
gen_corpus.py — 질의 코퍼스 병합 생성기 (Tier-2 SSOT 허브)
================================================================================
목적: "질의/시나리오/compose/capability" 로 흩어진 테스트 대상을, canonical
      source(각 repo 소유) + hand overlay(query_overlay.jsonc) 를 병합해
      단일 공유 아티팩트 `corpus/query_corpus.generated.json` 으로 만든다.
      이 아티팩트를 AI 챔피언·lab·be-3d·studio·gateway 모든 서브폴더가 소비.

파생 관계(단방향):
  be-3d op_registry.json (96 op, consumerClass, runtimeApi)  ─┐
  gateway router_meta.json (43 라우터 클래스)                 ├─→ query_corpus.generated.json
  be-3d region_camera.ts (34 region)                          │      └→ (모든 서브폴더가 HTTP 러너로 소비)
  studio METRIC_LABEL / be-3d metric_catalog (15 metric)      │
  studio executor_keys.ts (7 executor)                        │
  play100_manifest.ts ∪ scenario_nl_generated.jsonl (B-op NL) │
  corpus/query_overlay.jsonc (HAND: probeQuery·fixtures)     ─┘

핵심 게이트(사용자 요구 '수정 시 전수'):
  · A/C opcode(11) 는 overlay 에 probeQuery 필수 — 없으면 FAIL(미커버 opcode 노출)
  · B opcode(85) 는 play100/scenario_nl 이 emit 하는 op 로 커버 산출 → 차집합=무테스트
  · executor(7) ⊆ router 클래스(43) 매핑 검증

Usage:
  python corpus/gen_corpus.py            # 병합 → query_corpus.generated.json
  python corpus/gen_corpus.py --check    # 재생성 후 diff 0 검증(CI/pre-commit)
  python corpus/gen_corpus.py --coverage # opcode 커버리지 리포트만(라이브 불요)
Exit: 0 = OK, 1 = 미커버 A/C opcode 존재 or --check drift

설계 정본: energy-decision-studio/docs/QUERY_CORPUS_SSOT.md
공유 근거: myjob/docs/SSOT_GOVERNANCE.md §9 (도메인 중립 → energy-contracts)
"""
from __future__ import annotations
import json, re, sys, argparse, hashlib
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# energy-contracts/corpus/ → workspace 루트 = parents[2]
HERE = Path(__file__).resolve().parent
EC   = HERE.parent                       # projects/energy-contracts
WS   = EC.parent.parent                  # myjob 워크스페이스 루트
PROJ = WS / "projects"

OVERLAY_PATH = HERE / "query_overlay.jsonc"
OUT_PATH     = HERE / "query_corpus.generated.json"

# canonical source 경로(각 repo 소유 — 손대지 않음, 읽기만)
OP_REGISTRY  = PROJ / "building-energy-3d/frontend/src/_shared/op_registry.json"
ROUTER_META  = WS / "8.simulation/ems_transformer/serving/klue_router_v1/router_meta.json"
REGION_CAM   = PROJ / "building-energy-3d/frontend/src/lab-overlays/region_camera.ts"
EXECUTOR_KEY = PROJ / "energy-decision-studio/lib/actions/executor_keys.ts"
STUDIO_INTENT= PROJ / "energy-decision-studio/lib/intent.ts"
PLAY100      = PROJ / "building-energy-3d/frontend/src/lab-overlays/play100_manifest.ts"
SCENARIO_NL  = PROJ / "building-energy-3d/data/training/scenario_nl_generated.jsonl"


def _strip_jsonc(txt: str) -> str:
    """// 라인 주석 제거(문자열 내 // 는 보존)."""
    out = []
    for line in txt.splitlines():
        # 문자열 밖의 // 만 절단: 간단히 따옴표 홀짝 추적
        in_str = False; esc = False; cut = None
        for i, ch in enumerate(line):
            if esc:
                esc = False; continue
            if ch == "\\":
                esc = True; continue
            if ch == '"':
                in_str = not in_str; continue
            if ch == "/" and not in_str and i + 1 < len(line) and line[i + 1] == "/":
                cut = i; break
        out.append(line[:cut] if cut is not None else line)
    # 트레일링 콤마 제거
    joined = "\n".join(out)
    joined = re.sub(r",(\s*[}\]])", r"\1", joined)
    return joined


def load_overlay() -> dict:
    return json.loads(_strip_jsonc(OVERLAY_PATH.read_text(encoding="utf-8")))


def load_op_registry() -> tuple[list[dict], dict]:
    """96 op → runtimeApi 이름으로 정규화. consumerClass 포함."""
    d = json.loads(OP_REGISTRY.read_text(encoding="utf-8"))
    ops = d["ops"]
    norm = []
    by_class = {"A": [], "B": [], "C": []}
    for o in ops:
        api = o.get("runtimeApi") or o["name"]
        cc = o.get("consumerClass", "?")
        norm.append({"api": api, "name": o["name"], "ns": o["ns"],
                     "consumerClass": cc, "summary": (o.get("summary") or "")[:80]})
        by_class.setdefault(cc, []).append(api)
    return norm, by_class


def load_router_classes() -> list[str]:
    d = json.loads(ROUTER_META.read_text(encoding="utf-8"))
    lbl = d.get("id2label") or {}
    return sorted(set(lbl.values()))


def load_executors() -> list[str]:
    txt = EXECUTOR_KEY.read_text(encoding="utf-8")
    m = re.search(r"EXECUTOR_KEYS\s*=\s*\[(.*?)\]", txt, re.S)
    return re.findall(r'"([a-z_0-9]+)"', m.group(1)) if m else []


def load_metrics() -> list[str]:
    txt = STUDIO_INTENT.read_text(encoding="utf-8")
    m = re.search(r"METRIC_LABEL[^{]*\{(.*?)\n\}", txt, re.S)
    if not m:
        return []
    # METRIC_LABEL 은 한 줄에 여러 key 를 담음(key: "라벨", key2: "라벨") → 전역 매칭.
    #   값은 한국어 문자열이라 key([a-z_]+ 뒤 :)만 안전하게 잡힘.
    keys = re.findall(r"(?:^|[{,]|\n)\s*([a-z][a-z_0-9]*)\s*:", m.group(1))
    seen: list[str] = []
    for k in keys:
        if k not in seen:
            seen.append(k)
    return seen


def load_regions() -> list[dict]:
    """region_camera.ts REGION_CAMERA → [{region, lon, lat, alt}]."""
    if not REGION_CAM.exists():
        return []
    txt = REGION_CAM.read_text(encoding="utf-8")
    m = re.search(r"REGION_CAMERA[^{]*\{(.*?)\n\};", txt, re.S)
    if not m:
        return []
    out = []
    for rm in re.finditer(r"(\w+):\s*\[([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\]", m.group(1)):
        out.append({"region": rm.group(1), "lon": float(rm.group(2)),
                    "lat": float(rm.group(3)), "alt": float(rm.group(4))})
    return out


_OP_TOKEN = re.compile(r'"(?:api|op)"?\s*:\s*"([A-Za-z][A-Za-z0-9_.]+)"|(?:api|op):\s*"([A-Za-z][A-Za-z0-9_.]+)"')


def _ops_emitted_in(path: Path) -> set[str]:
    """play100.ts / scenario_nl.jsonl 이 언급하는 op/api 이름 집합(대략)."""
    if not path.exists():
        return set()
    txt = path.read_text(encoding="utf-8", errors="replace")
    found: set[str] = set()
    for a, b in _OP_TOKEN.findall(txt):
        tok = a or b
        if tok:
            found.add(tok)
    return found


def compute_bop_coverage(op_apis: list[str]) -> dict:
    """B-op 커버리지: play100 ∪ scenario_nl 가 언급하는 op ∩ 전체 op → 미커버 산출."""
    emitted = _ops_emitted_in(PLAY100) | _ops_emitted_in(SCENARIO_NL)
    # runtimeApi 와 namespaced name 둘 다로 매칭 시도
    covered = set()
    for api in op_apis:
        short = api.split(".")[-1]
        if api in emitted or short in emitted or any(short.lower() in e.lower() for e in emitted):
            covered.add(api)
    uncovered = [a for a in op_apis if a not in covered]
    return {"emittedTokens": len(emitted), "covered": sorted(covered),
            "uncovered": sorted(uncovered)}


def build() -> tuple[dict, list[str]]:
    problems: list[str] = []
    overlay = load_overlay()
    ops, by_class = load_op_registry()
    routers = load_router_classes()
    executors = load_executors()
    metrics = load_metrics()
    regions = load_regions()

    op_apis = [o["api"] for o in ops]
    ac_apis = [o["api"] for o in ops if o["consumerClass"] in ("A", "C")]
    b_apis  = [o["api"] for o in ops if o["consumerClass"] == "B"]

    # ── 게이트 1: A/C opcode(11) probeQuery 필수 ────────────────────────────
    op_probes = overlay.get("opProbes", {})
    missing_ac = [a for a in ac_apis if a not in op_probes]
    if missing_ac:
        problems.append(f"A/C opcode {len(missing_ac)}종 probeQuery 누락: {missing_ac}")
    stale_probes = [k for k in op_probes if k not in op_apis]
    if stale_probes:
        problems.append(f"overlay opProbes 에 registry 밖 op(고아): {stale_probes}")

    # ── 게이트 2: executor(7) ⊆ router 클래스(43) 매핑 ──────────────────────
    #   executor 이름 ↔ router 클래스 이름은 다를 수 있어 별칭 허용 매핑.
    EXEC_ROUTER_ALIAS = {
        "apply_policy_lever": {"policy_evaluate", "apply_policy_lever"},
        "counterfactual":     {"counterfactual"},
        "recommend_retrofit": {"ems_recommend"},
        "identify_ems":       {"ems_identify"},
        "forecast_24h":       {"forecast_24h", "load_predict"},
        "diagnose_anomaly":   {"anomaly", "ems_diagnose"},
        "mpc_optimize":       {"mpc_optimize", "mpc", "ems_optimize"},
    }
    rset = set(routers)
    for ex in executors:
        alias = EXEC_ROUTER_ALIAS.get(ex, {ex})
        if not (alias & rset):
            problems.append(f"executor '{ex}' 가 router_meta.json 43클래스에 매핑 없음(별칭 {alias})")

    # ── 게이트 3: capabilityProbes 7종 == executor 7종 ──────────────────────
    cap_probes = overlay.get("capabilityProbes", {})
    miss_cap = [e for e in executors if e not in cap_probes]
    if miss_cap:
        problems.append(f"capabilityProbes 누락 executor: {miss_cap}")

    # ── B-op 커버리지 산출(경고만; 게이트 아님) ─────────────────────────────
    bcov = compute_bop_coverage(b_apis)

    corpus = {
        "schema": 1,
        "note": "AUTO-GENERATED by corpus/gen_corpus.py — 손으로 고치지 말 것(overlay 를 고쳐라).",
        "sources": {
            "op_registry": str(OP_REGISTRY.relative_to(WS)),
            "router_meta": str(ROUTER_META.relative_to(WS)),
            "region_camera": str(REGION_CAM.relative_to(WS)) if REGION_CAM.exists() else None,
            "executor_keys": str(EXECUTOR_KEY.relative_to(WS)),
        },
        "counts": {
            "opcodes": len(op_apis), "opA": len(by_class.get("A", [])),
            "opB": len(by_class.get("B", [])), "opC": len(by_class.get("C", [])),
            "routerClasses": len(routers), "executors": len(executors),
            "metrics": len(metrics), "regions": len(regions),
            "queryClasses": len(overlay.get("queryClasses", [])),
            "refuseProbes": len(overlay.get("refuseProbes", [])),
        },
        # ── 기계 병합 층 ──
        "opcodes": ops,                       # 96, api+consumerClass+ns+summary
        "routerClasses": routers,             # 43
        "executors": executors,               # 7
        "metrics": metrics,                   # 15
        "regions": regions,                   # 34 (region+lon/lat/alt)
        # ── overlay(판단) 층 ──
        "opProbes": op_probes,                # A/C 11 probeQuery
        "capabilityProbes": cap_probes,       # 7 executor probeQuery
        "fixtures": overlay.get("fixtures", {}),
        "queryClasses": overlay.get("queryClasses", []),   # C/S/L 24
        "refuseProbes": overlay.get("refuseProbes", []),
        # ── 커버리지 리포트 ──
        "coverage": {
            "acProbed": [a for a in ac_apis if a in op_probes],
            "acMissing": missing_ac,
            "bop": bcov,
        },
    }
    return corpus, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="재생성 후 diff 0 검증")
    ap.add_argument("--coverage", action="store_true", help="커버리지 리포트만 출력")
    args = ap.parse_args()

    corpus, problems = build()
    new_json = json.dumps(corpus, ensure_ascii=False, indent=2, sort_keys=False)

    if args.coverage:
        c = corpus["counts"]; cov = corpus["coverage"]
        print("=" * 70)
        print(f"  질의 코퍼스 커버리지 — opcode {c['opcodes']} (A{c['opA']}/B{c['opB']}/C{c['opC']})")
        print(f"  router {c['routerClasses']}  executor {c['executors']}  "
              f"metric {c['metrics']}  region {c['regions']}  queryClass {c['queryClasses']}")
        print("-" * 70)
        print(f"  A/C probeQuery: {len(cov['acProbed'])}/{c['opA']+c['opC']} 커버")
        if cov["acMissing"]:
            print(f"  ❌ A/C 미커버: {cov['acMissing']}")
        b = cov["bop"]
        print(f"  B-op: play100∪scenario_nl 토큰 {b['emittedTokens']}개 → "
              f"{len(b['covered'])}/{c['opB']} 커버, {len(b['uncovered'])} 무테스트")
        if b["uncovered"]:
            print(f"     무테스트 B-op(대표질의 후보): {b['uncovered'][:20]}"
                  + (" …" if len(b["uncovered"]) > 20 else ""))
        print("=" * 70)

    if args.check:
        if not OUT_PATH.exists():
            print("❌ query_corpus.generated.json 부재 — gen_corpus.py 먼저 실행"); sys.exit(1)
        old = OUT_PATH.read_text(encoding="utf-8")
        if old.strip() != new_json.strip():
            print("❌ DRIFT: query_corpus.generated.json 이 overlay/canonical 과 불일치. "
                  "→ python corpus/gen_corpus.py 재실행 후 커밋"); sys.exit(1)
        print("✅ --check: drift 0")
    else:
        OUT_PATH.write_text(new_json + "\n", encoding="utf-8")
        h = hashlib.sha256(new_json.encode()).hexdigest()[:12]
        print(f"✅ 생성: {OUT_PATH.relative_to(WS)}  ({len(new_json):,} bytes, sha={h})")

    if problems:
        print("\n".join(f"  ⚠ {p}" for p in problems))
        # A/C 미커버는 hard fail, 나머지는 경고
        if any("probeQuery 누락" in p or "고아" in p for p in problems):
            sys.exit(1)


if __name__ == "__main__":
    main()
