#!/usr/bin/env python
"""self-hosted runner 크래시 루프 복구 — 컨테이너 재생성(설정 초기화).

2026-08-01: 17개 러너가 전부 이 상태로 죽어 있었고, 그 결과 **필수 체크가 아예 생성되지 않아
PR 머지가 admin 으로도 불가능**했다("Required status check is expected"). CI 침묵은 조용해서
더 위험하다 — 정기 점검 대상.

증상: myoung34/github-runner 컨테이너가 재시작마다
  "Cannot configure the runner because it is already configured"
  "Value cannot be null. (Parameter 'configuredSettings')"
→ 컨테이너 내부 .runner 설정이 반쯤 쓰인 채 남아 재구성이 막힌 상태. 볼륨 마운트가 없으므로
  **컨테이너를 지우고 같은 설정으로 다시 만들면** 깨끗한 파일시스템에서 재등록된다.

토큰(ACCESS_TOKEN)은 기존 컨테이너 env 에서 그대로 옮기며 **출력하지 않는다**.

사용: python fix_runners.py --list | --fix <name>... | --fix-all
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SECRET_KEYS = ("ACCESS_TOKEN", "RUNNER_TOKEN", "GITHUB_TOKEN", "PAT")
# 이미지가 스스로 넣는 환경변수 — 재생성 시 넘기면 안 되는 것들(중복/충돌 방지)
SKIP_KEYS = ("PATH", "LANG", "LANGUAGE", "LC_ALL", "DEBIAN_FRONTEND", "HOSTNAME", "HOME")


def sh(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout.strip()


def runners() -> list[dict]:
    names = [n for n in sh(["docker", "ps", "-a", "--filter", "name=gh-runner",
                            "--format", "{{.Names}}"]).splitlines() if n]
    out = []
    for n in names:
        raw = sh(["docker", "inspect", n])
        try:
            d = json.loads(raw)[0]
        except Exception:
            continue
        out.append({
            "name": n,
            "state": d["State"]["Status"],
            "restarting": d["State"]["Status"] == "restarting",
            "image": d["Config"]["Image"],
            "env": d["Config"]["Env"] or [],
            "restart": (d["HostConfig"]["RestartPolicy"] or {}).get("Name", "always"),
            "repo": next((e.split("=", 1)[1] for e in d["Config"]["Env"]
                          if e.startswith("REPO_URL=")), ""),
        })
    return out


def recreate(r: dict) -> tuple[bool, str]:
    env_args: list[str] = []
    has_token = False
    for e in r["env"]:
        k = e.split("=", 1)[0]
        if k in SKIP_KEYS:
            continue
        if k in SECRET_KEYS:
            has_token = True
        env_args += ["-e", e]                      # 값은 인자로만 전달(출력 없음)
    if not has_token:
        return False, "토큰 env 없음 — 수동 재등록 필요"
    subprocess.run(["docker", "rm", "-f", r["name"]], capture_output=True, text=True)
    p = subprocess.run(
        ["docker", "run", "-d", "--name", r["name"], "--restart", r["restart"] or "always",
         *env_args, r["image"]],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return False, (p.stderr or "").strip()[:120]
    return True, "재생성"


EXPECTED = Path(__file__).resolve().parent / "runners.expected.json"


def load_expected() -> list[dict]:
    """기대 인벤토리. **없으면 '사라진 러너'는 정의상 보이지 않는다** —
    2026-08-01 에 17→14 소멸을 아무도 못 본 이유가 정확히 이것이다(살아있는 것만 셌다)."""
    if not EXPECTED.exists():
        return []
    return json.loads(EXPECTED.read_text(encoding="utf-8")).get("runners", [])


def gh_runners(repo: str) -> list[dict]:
    """GitHub 에 등록된 러너 상태. docker 만 보면 'Up 인데 offline' 을 못 잡는다."""
    p = subprocess.run(["gh", "api", f"repos/jukkim/{repo}/actions/runners"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return []
    try:
        return json.loads(p.stdout).get("runners", [])
    except Exception:
        return []


def cmd_verify(repo_filter: str | None) -> int:
    """기대 인벤토리 ↔ 살아있는 컨테이너 ↔ GitHub 등록 3자 대조.

    세 가지를 각각 다르게 본다:
      · 컨테이너 소멸  = 인벤토리에 있는데 docker 에 없음 (오늘 3건 발생)
      · 컨테이너 죽음  = docker 에 있으나 Up 아님
      · **등록 죽음**  = Up 인데 GitHub 는 offline (필수 체크가 영원히 pending 되는 상태)
    """
    exp = load_expected()
    if not exp:
        print(f"⚠ 기대 인벤토리 없음({EXPECTED.name}) — 소멸 탐지 불가. --list 후 생성 권장")
        return 0
    if repo_filter:
        exp = [r for r in exp if r["repo"] == repo_filter]
        if not exp:
            return 0
    alive = {r["name"]: r for r in runners()}
    problems: list[str] = []
    checked_repos: dict[str, list[dict]] = {}
    for e in exp:
        c = alive.get(e["container"])
        if c is None:
            problems.append(f"소멸: {e['container']} ({e['repo']})")
            continue
        if c["state"] != "running":
            problems.append(f"죽음: {e['container']} state={c['state']}")
            continue
        if e["repo"] not in checked_repos:
            checked_repos[e["repo"]] = gh_runners(e["repo"])
        reg = next((g for g in checked_repos[e["repo"]] if g.get("name") == e["runnerName"]), None)
        if reg is None:
            problems.append(f"미등록: {e['runnerName']} ({e['repo']}) — 컨테이너는 Up")
        elif reg.get("status") != "online":
            problems.append(f"등록 offline: {e['runnerName']} ({e['repo']}) — 컨테이너는 Up, "
                            f"busy={reg.get('busy')} → 필수 체크가 pending 으로 멈춘다")
    if not problems:
        print(f"✅ 러너 {len(exp)}개 정상(컨테이너 Up + GitHub online)")
        return 0
    print(f"❌ 러너 이상 {len(problems)}건:")
    for m in problems:
        print("  -", m)
    print("  복구: python scripts/fix_gh_runners.py --fix-all   (소멸은 --fix <name> 로 재생성)")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="기대 인벤토리 ↔ 컨테이너 ↔ GitHub 등록 3자 대조(이상 시 exit 1)")
    ap.add_argument("--repo", default=None, help="--verify 를 특정 repo 로 한정")
    ap.add_argument("--fix", nargs="*", metavar="NAME")
    ap.add_argument("--fix-all", action="store_true", help="restarting 상태 전부")
    a = ap.parse_args()

    if a.verify:
        return cmd_verify(a.repo)

    rs = runners()
    if a.list or (not a.fix and not a.fix_all):
        bad = [r for r in rs if r["restarting"]]
        names = {r["name"] for r in rs}
        gone = [e["container"] for e in load_expected() if e["container"] not in names]
        print(f"러너 {len(rs)}개 — 정상 {len(rs)-len(bad)} / 크래시루프 {len(bad)}"
              + (f" / **소멸 {len(gone)}**" if gone else ""))
        for g in gone:
            print(f"  ⛔ {g:38s} 컨테이너 자체가 없음(인벤토리 기준)")
        for r in rs:
            mark = "❌" if r["restarting"] else "✅"
            print(f"  {mark} {r['name']:38s} {r['state']:12s} {r['repo'].split('/')[-1]}")
        return 0

    targets = ([r for r in rs if r["restarting"]] if a.fix_all
               else [r for r in rs if r["name"] in (a.fix or [])])
    print(f"대상 {len(targets)}개 재생성")
    ok = 0
    for r in targets:
        good, msg = recreate(r)
        print(f"  {'✅' if good else '❌'} {r['name']:38s} {msg}")
        ok += 1 if good else 0
    print(f"완료 {ok}/{len(targets)}")
    return 0 if ok == len(targets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
