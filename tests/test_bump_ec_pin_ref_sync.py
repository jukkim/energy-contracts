"""bump_ec_pin 의 pin↔ssot-drift ref 동반 갱신 가드 (2026-07-31).

배경: pyproject 의 EC pin 만 bump 하고 각 consumer `.github/workflows/ssot-drift.yml`
의 EC checkout `ref:` 를 안 바꾸면, CI 가 **옛 태그 스키마**로 gen_constants --check 를
돌려 regen 된 생성본을 DRIFT 로 오탐한다. 2026-07-21(v0.3.20)·2026-07-31(v0.3.23,
6 PR 연속 red) 두 차례 재발 → 본 테스트가 정규식·동반 갱신을 고정한다.
"""
from __future__ import annotations

import importlib.util
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("bump_ec_pin", _ROOT / "scripts" / "bump_ec_pin.py")
assert _SPEC and _SPEC.loader
bump = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bump)


_WF_SAMPLE = """\
jobs:
  ssot-drift:
    steps:
      - name: Checkout self
        uses: actions/checkout@v4
        with:
          path: projects/edge-agent

      - name: Checkout energy-contracts (public SSOT)
        uses: actions/checkout@v4
        with:
          repository: jukkim/energy-contracts
          ref: v0.3.22  # pyproject.toml 핀과 lockstep
          path: projects/energy-contracts
"""


def test_ref_regex_matches_ec_checkout() -> None:
    found = [m.group(2) for m in bump._WF_REF_RE.finditer(_WF_SAMPLE)]
    assert found == ["v0.3.22"]


def test_ref_regex_substitutes_keeping_comment() -> None:
    out = bump._WF_REF_RE.sub(lambda m: m.group(1) + "v0.3.23", _WF_SAMPLE)
    assert "ref: v0.3.23  # pyproject.toml 핀과 lockstep" in out
    assert "v0.3.22" not in out


def test_ref_regex_ignores_other_repo_checkout() -> None:
    """다른 repo checkout 의 ref 는 건드리지 않는다 (오탐 치환 금지)."""
    other = _WF_SAMPLE.replace("jukkim/energy-contracts", "jukkim/some-other-repo")
    assert bump._WF_REF_RE.sub(lambda m: m.group(1) + "v9.9.9", other) == other


def test_workspace_pin_and_ref_are_lockstep() -> None:
    """실제 워크스페이스 상태 — pin 과 ssot-drift ref 가 같은 태그여야 한다."""
    pins = {v for v in bump.current_pins().values() if v}
    refs = {r for v in bump.current_wf_refs().values() for r in v}
    if not pins or not refs:  # consumer repo 미체크아웃 환경(CI 단독 clone)
        return
    assert len(pins) == 1, f"pin lockstep 위반: {pins}"
    assert refs <= pins, f"ssot-drift ref 가 pin 과 skew: ref={refs} pin={pins}"
