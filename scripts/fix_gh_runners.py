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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fix", nargs="*", metavar="NAME")
    ap.add_argument("--fix-all", action="store_true", help="restarting 상태 전부")
    a = ap.parse_args()

    rs = runners()
    if a.list or (not a.fix and not a.fix_all):
        bad = [r for r in rs if r["restarting"]]
        print(f"러너 {len(rs)}개 — 정상 {len(rs)-len(bad)} / 크래시루프 {len(bad)}")
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
