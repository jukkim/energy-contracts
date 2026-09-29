#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""소비자 **잠금 파일**(`contracts/energy_contracts.lock.json`)을 태그와 같이 움직인다.

## 왜 따로 있는가 — 핀이 pyproject 에만 있는 게 아니다

`bump_ec_pin.py` 는 pyproject 핀·ssot-drift `ref:`·CI pip 핀만 알았다. airos-energy-decision 은 EC 를
**잠금 파일**(EC 커밋 + 스키마별 sha256)로 고정한다. 그래서 EC 를 릴리스할 때마다:

    생성 상수(_generated_constants.py)   → 새 태그로 regen 됨
    잠금 파일 commit                      → 옛 커밋 그대로
    AIROS CI                              → 잠금 커밋으로 EC 를 옮겨 gen_constants --check → DRIFT (빨강)

2026-09-29 실측: v0.3.62 bump 뒤 AIROS `SSOT Drift Check` 빨강(run 36554706022) — 잠금이 v0.3.60(57f8840) 에 있었다.

## 규칙

- 잠금 파일은 **찾아서** 다룬다(`projects/*/contracts/energy_contracts.lock.json`) — 손으로 적은 목록에 없어서
  조용히 빠지는 일(mgcc·building-energy-sejong·ingestion-worker 선례)을 되풀이하지 않는다.
- 해시 함수는 **소비자의 것을 그대로 불러 쓴다**(`src/<pkg>/contracts_client.py` 의 `pin_hash`).
  사본을 두지 않는다 — 소비자가 해시 기준(`HASH_BASIS`)을 바꾸면 이 도구도 같이 바뀐다.
  잠금 파일의 `hash_basis` 가 그 모듈의 `HASH_BASIS` 와 다르면 멈춘다(모르는 기준으로 쓰지 않는다).
- 스키마 집합은 **잠금이 선언한 그대로** 둔다. 새 커밋에 그 스키마가 없으면 멈춘다(조용히 빼지 않는다).
- 스키마 바이트는 작업 트리가 아니라 **태그 커밋의 git 객체**에서 읽는다(소비자 `pinned_schema_bytes` 와 같은 원천).
- 태그 커밋으로 옮기면 스키마별 커밋 덮어쓰기(`schema_commits`)와 브랜치 표시(`branch`)는 뜻을 잃는다 → 지운다.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Callable

LOCK_REL = Path("contracts") / "energy_contracts.lock.json"
SCHEMA_DIR_IN_REPO = "energy_contracts/schemas"
#: 태그 커밋으로 옮기면 뜻을 잃는 칸 — 옛 커밋·브랜치를 가리킨다.
_STALE_ON_RETARGET = ("schema_commits", "branch")


class LockError(RuntimeError):
    """잠금 파일을 안전하게 다시 만들 수 없다(해시 모듈 없음·기준 불일치·스키마 없음·태그 없음)."""


def consumer_locks(projects: Path) -> list[Path]:
    """워크스페이스의 모든 소비자 잠금 파일(찾아서 — 목록으로 적지 않는다)."""
    return sorted(projects.glob(f"*/{LOCK_REL.as_posix()}"))


def repo_of(lock_path: Path) -> Path:
    return lock_path.parents[1]


def load_hasher(repo_root: Path) -> tuple[Callable[[bytes], str], str, Path]:
    """소비자의 `contracts_client.pin_hash`·`HASH_BASIS` 를 **그 파일에서** 불러온다.

    반환 = (pin_hash, HASH_BASIS, 모듈 파일 경로). 모듈이 없거나 둘 이상이면 LockError — 짐작하지 않는다.
    """
    found = sorted(repo_root.glob("src/*/contracts_client.py"))
    if len(found) != 1:
        raise LockError(f"{repo_root.name}: src/*/contracts_client.py 가 {len(found)}개 — 해시 함수를 정할 수 없다")
    module_path = found[0]
    name = f"_ec_consumer_contracts_client_{repo_root.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise LockError(f"{module_path}: 모듈을 불러올 수 없다")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    hasher = getattr(module, "pin_hash", None)
    basis = getattr(module, "HASH_BASIS", None)
    if not callable(hasher) or not isinstance(basis, str):
        raise LockError(f"{module_path}: pin_hash·HASH_BASIS 가 없다")
    return hasher, basis, module_path


def resolve_commit(contracts_root: Path, ref: str) -> str:
    r = subprocess.run(["git", "-C", str(contracts_root), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                       capture_output=True, text=True)
    sha = r.stdout.strip()
    if r.returncode != 0 or len(sha) != 40:
        raise LockError(f"energy-contracts 에서 {ref} 를 커밋으로 풀 수 없다")
    return sha


def schema_bytes_at(contracts_root: Path, commit: str, name: str) -> bytes:
    if Path(name).name != name:
        raise LockError(f"스키마 이름에 경로가 있다: {name}")
    r = subprocess.run(["git", "-C", str(contracts_root), "show", f"{commit}:{SCHEMA_DIR_IN_REPO}/{name}"],
                       capture_output=True)
    if r.returncode != 0:
        raise LockError(f"{commit[:7]} 에 {SCHEMA_DIR_IN_REPO}/{name} 이 없다 — 잠금의 스키마 집합을 조용히 줄이지 않는다")
    return r.stdout


def expected_lock(lock: dict, contracts_root: Path, commit: str,
                  hasher: Callable[[bytes], str], basis: str) -> dict:
    """`commit` 으로 옮긴 잠금 — 칸 순서·스키마 집합·설명은 그대로, commit·해시만 새로."""
    if lock.get("hash_basis") != basis:
        raise LockError(f"잠금 hash_basis={lock.get('hash_basis')!r} 가 소비자 HASH_BASIS={basis!r} 와 다르다")
    schemas = lock.get("schemas")
    if not isinstance(schemas, dict) or not schemas:
        raise LockError("잠금에 schemas 가 없다")
    out: dict = {}
    for key, value in lock.items():
        if key in _STALE_ON_RETARGET:
            continue
        if key == "commit":
            out[key] = commit
        elif key == "schemas":
            out[key] = {name: hasher(schema_bytes_at(contracts_root, commit, name)) for name in schemas}
        else:
            out[key] = value
    return out


def render(lock: dict) -> str:
    """잠금 파일의 글 모양(들여쓰기 2·한글 그대로·끝 줄바꿈) — 지금 커밋된 파일과 같은 모양."""
    return json.dumps(lock, indent=2, ensure_ascii=False) + "\n"


def _read_keep_newlines(p: Path) -> str:
    with p.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_keep_newlines(p: Path, s: str) -> None:
    with p.open("w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def diff(current: dict, expected: dict) -> list[str]:
    """현재 잠금과 기대 잠금의 차이를 사람 말로(검사 대상 이름을 남긴다)."""
    problems: list[str] = []
    if current.get("commit") != expected.get("commit"):
        problems.append(f"commit {str(current.get('commit'))[:7]} ≠ 태그 {str(expected.get('commit'))[:7]}")
    for key in _STALE_ON_RETARGET:
        if key in current:
            problems.append(f"옛 칸 {key} 가 남아 있다")
    cur_s, exp_s = current.get("schemas") or {}, expected.get("schemas") or {}
    for name in exp_s:
        if cur_s.get(name) != exp_s[name]:
            problems.append(f"{name} 해시 불일치")
    return problems


def check(contracts_root: Path, projects: Path, ref: str | None) -> tuple[int, int]:
    """모든 잠금이 `ref` 와 맞는지. 반환 = (검사한 잠금 수, 위반 수). 못 재는 것도 위반으로 센다(못 잼 ≠ 통과)."""
    locks = consumer_locks(projects)
    violations = 0
    for lock_path in locks:
        rel = f"{repo_of(lock_path).name}/{LOCK_REL.as_posix()}"
        if not ref:
            print(f"  ✗ {rel}: 핀이 하나로 모이지 않아 잠금의 목표 태그를 정할 수 없다(못 잼)")
            violations += 1
            continue
        try:
            current = json.loads(_read_keep_newlines(lock_path))
            hasher, basis, _ = load_hasher(repo_of(lock_path))
            commit = resolve_commit(contracts_root, ref)
            want = expected_lock(current, contracts_root, commit, hasher, basis)
        except (LockError, ValueError, OSError) as exc:
            print(f"  ✗ {rel}: {exc}")
            violations += 1
            continue
        problems = diff(current, want)
        if problems:
            violations += 1
            print(f"  ✗ {rel}: {ref} 와 어긋남 — {'; '.join(problems[:6])}"
                  + (f" 외 {len(problems) - 6}건" if len(problems) > 6 else ""))
            print("    → CI 가 잠금 커밋으로 EC 를 옮겨 생성본을 재면 DRIFT 가 난다. bump 로 동반 갱신할 것.")
        else:
            print(f"  잠금 확인: {rel} → {ref} ({commit[:7]}) · 스키마 {len(want['schemas'])}건 해시 일치")
    return len(locks), violations


def bump(contracts_root: Path, projects: Path, ref: str) -> list[str]:
    """모든 잠금을 `ref` 로 옮긴다(줄끝 보존). 바뀐 저장소 이름 목록. 하나라도 못 만들면 LockError — 반쯤 쓰지 않는다."""
    commit = resolve_commit(contracts_root, ref)
    planned: list[tuple[Path, str, str]] = []
    for lock_path in consumer_locks(projects):
        raw = _read_keep_newlines(lock_path)
        hasher, basis, _ = load_hasher(repo_of(lock_path))
        text = render(expected_lock(json.loads(raw), contracts_root, commit, hasher, basis))
        if "\r\n" in raw:
            text = text.replace("\n", "\r\n")
        planned.append((lock_path, raw, text))
    changed: list[str] = []
    for lock_path, raw, text in planned:
        if text != raw:
            _write_keep_newlines(lock_path, text)
            changed.append(repo_of(lock_path).name)
    return changed
