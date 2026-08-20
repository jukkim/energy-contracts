# -*- coding: utf-8 -*-
"""패키지 **version 이 태그를 따라가는가**.

## 왜 이 시험이 있는가

`v0.3.41` 태그를 냈는데 `pyproject.toml` 의 `version` 은 `0.3.40` 그대로였다
(2026-08-21). 그래서 그 태그로 설치하면 패키지 버전이 **0.3.40** 으로 잡히고,
소비자의 정직성 시험(`설치된 EC == 핀`)이 **구조적으로 영원히 실패**했다.

⚠ 태그와 버전이 어긋나면 "무엇이 설치됐는지" 를 아무도 못 말한다 —
   핀은 v0.3.41 인데 설치본은 0.3.40 이라고 답하는 상태가 된다.
   **핀이 서로 같은 것과 핀이 옳은 것이 다르듯**, 태그가 있는 것과 버전이 맞는 것도 다르다.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _declared_version() -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"',
                  (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M)
    assert m, "pyproject.toml 에서 version 을 못 읽었다"
    return m.group(1)


def _latest_tag() -> str | None:
    r = subprocess.run(["git", "-C", str(ROOT), "tag", "--sort=-v:refname"],
                       capture_output=True, timeout=60)
    if r.returncode != 0:
        return None
    tags = [t for t in r.stdout.decode("utf-8", "replace").split() if t.startswith("v")]
    return tags[0] if tags else None


def test_declared_version_is_not_behind_the_latest_tag():
    """선언 version 이 최신 태그보다 **뒤처지지 않는가**.

    같거나 앞서면 통과다(다음 릴리스를 미리 올려 둔 상태를 막지 않는다).
    뒤처지면 실패 — 그 상태에서 태그를 내면 설치본이 거짓말을 한다.
    """
    tag = _latest_tag()
    if tag is None:
        # git 이 없으면 **못 잰 것**이지 통과가 아니다 — 그대로 적고 넘어간다.
        import pytest
        pytest.skip("git 태그를 못 읽었다 — 이 시험은 못 쟀다(통과 아님)")
    tv = tuple(int(x) for x in tag.lstrip("v").split(".") if x.isdigit())
    dv = tuple(int(x) for x in _declared_version().split(".") if x.isdigit())
    assert dv >= tv, (
        f"pyproject version {_declared_version()} 이 최신 태그 {tag} 보다 뒤처졌다. "
        "이 상태로 태그를 내면 그 태그로 설치한 소비자가 **옛 버전 문자열**을 보고, "
        "'설치된 것 == 핀' 을 검사하는 쪽이 구조적으로 영원히 실패한다.")
