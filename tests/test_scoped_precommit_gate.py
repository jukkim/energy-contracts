"""pre-commit 게이트의 **범위** 시험 (2026-09-15).

형제 체크아웃(8.simulation `_shared`)의 drift 가 무관한 저장소 커밋을 막아 `--no-verify` 가
상습화됐다. 여기서는 가짜 워크스페이스(git 저장소 여러 개 + 링크드 워크트리)를 만들어

  - 형제 drift → 범위 검사 **초록** (막지 않는다)
  - 자기 drift → 범위 검사 **빨강** (막는다) — 워크트리에서 커밋해도 같다
  - 전수 검사(`gen_constants.py --check`, validate_ssot 인자 없음) → 형제 drift 도 **빨강**

을 모두 확인한다. 초록만 본 게이트는 게이트가 아니다.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import gen_constants as gc  # noqa: E402
import gen_constants_scoped as scoped  # noqa: E402
import validate_ssot  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None,
                                reason="못 잼(UNMEASURED): 저장소 정체 판정에 git 필요")

GEN_A = "projects/repo_a/src/_generated_constants.py"
GEN_B = "projects/repo_b/src/_generated_constants.py"
EXPECTED = {"repo_a": "A = 1\n", "repo_b": "B = 1\n"}
TARGETS = {"repo_a": {"python": GEN_A}, "repo_b": {"python": GEN_B}}


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "-c", "core.autocrlf=false", *args],
                   cwd=cwd, check=True, capture_output=True, env=scoped.clean_git_env())


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def _repo(parent: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        _write(parent / rel, text)
    _git(parent, "init", "-q")
    _git(parent, "add", "-A")
    _git(parent, "commit", "-q", "-m", "init")
    return parent


@pytest.fixture()
def ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    _repo(ws / "projects" / "repo_a", {"src/_generated_constants.py": EXPECTED["repo_a"]})
    _repo(ws / "projects" / "repo_b", {"src/_generated_constants.py": EXPECTED["repo_b"]})
    _repo(ws / "projects" / "repo_none", {"README.md": "x\n"})
    return ws


def _scoped(ws: Path, root: Path) -> int:
    return scoped.check_scoped(
        root, targets=TARGETS, workspace_root=ws, contracts_root=ws / "projects" / "no-ec",
        render=lambda proj, _lang, _cfg: EXPECTED[proj], projection_drift=lambda: False)


# ── gen_constants_scoped ─────────────────────────────────────────────────────

def test_green_when_own_target_matches(ws: Path):
    assert _scoped(ws, ws / "projects" / "repo_a") == 0


def test_sibling_drift_does_not_block(ws: Path):
    _write(ws / GEN_B, "B = 2\n")
    assert _scoped(ws, ws / "projects" / "repo_a") == 0
    assert _scoped(ws, ws / "projects" / "repo_b") == 1       # 그 형제 자신의 커밋은 막힌다


def test_own_drift_blocks(ws: Path):
    _write(ws / GEN_A, "A = 2\n")
    assert _scoped(ws, ws / "projects" / "repo_a") == 1


def test_own_missing_target_blocks(ws: Path):
    (ws / GEN_A).unlink()
    assert _scoped(ws, ws / "projects" / "repo_a") == 1


def test_repo_without_targets_passes(ws: Path, capsys):
    _write(ws / GEN_B, "B = 2\n")
    assert _scoped(ws, ws / "projects" / "repo_none") == 0
    assert "대상 없음" in capsys.readouterr().out


def test_subdirectory_root_resolves_to_repo(ws: Path):
    _write(ws / GEN_A, "A = 2\n")
    assert _scoped(ws, ws / "projects" / "repo_a" / "src") == 1


def test_linked_worktree_is_matched_by_repo_identity(ws: Path):
    main = ws / "projects" / "repo_a"
    wt = ws / "projects" / "wt_repo_a_topic"
    _git(main, "worktree", "add", "-q", "-b", "topic", str(wt))
    own = wt / "src" / "_generated_constants.py"

    s = scoped.Scope(wt, ws)
    assert s.map(GEN_A) == own.resolve()                      # 등록은 메인 경로, 비교는 워크트리 파일
    assert s.map(GEN_B) is None
    assert _scoped(ws, wt) == 0

    _write(own, "A = 2\n")                                    # 워크트리에서 커밋하려는 파일이 drift
    assert _scoped(ws, wt) == 1

    _write(own, EXPECTED["repo_a"])
    _write(ws / GEN_A, "A = 2\n")                             # 메인 체크아웃만 어긋남 → 워크트리 커밋과 무관
    _write(ws / GEN_B, "B = 2\n")                             # 형제도 어긋남
    assert _scoped(ws, wt) == 0


def test_hook_git_env_does_not_leak_into_identity(ws: Path, monkeypatch):
    """훅 안에서는 GIT_DIR·GIT_INDEX_FILE 이 export 돼 있다 — 그걸 따라가면 전부 한 저장소로 보인다."""
    monkeypatch.setenv("GIT_DIR", str(ws / "projects" / "repo_b" / ".git"))
    _write(ws / GEN_B, "B = 2\n")
    assert scoped.Scope(ws / "projects" / "repo_a", ws).map(GEN_B) is None
    assert _scoped(ws, ws / "projects" / "repo_a") == 0


def test_unscoped_check_still_sees_sibling_drift(ws: Path, monkeypatch):
    """전수 검사(CI·센티넬)는 바뀌지 않았다 — 형제 drift 도 빨강."""
    monkeypatch.setattr(gc, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(gc, "PROJECT_TARGETS",
                        {k: {**v, "_expect": EXPECTED[k]} for k, v in TARGETS.items()})
    monkeypatch.setattr(gc, "load_schemas", lambda: {})
    monkeypatch.setattr(gc, "gen_python", lambda _s: "")
    monkeypatch.setattr(gc, "apply_exports_filter", lambda _full, _lang, cfg: cfg["_expect"])
    monkeypatch.setattr(gc.legacy_e_codes, "sync_projection", lambda _check_only: False)
    assert gc.regenerate_all(check_only=True) == 0
    _write(ws / GEN_B, "B = 2\n")
    assert gc.regenerate_all(check_only=True) == 1


def test_contracts_repo_owns_projection_not_consumer_targets():
    s = scoped.Scope(ROOT)
    assert s.is_repo(gc.CONTRACTS_ROOT)
    for cfg in gc.PROJECT_TARGETS.values():
        for lang in ("python", "ts"):
            if cfg.get(lang):
                assert s.map(cfg[lang]) is None, cfg[lang]


def test_cli_rejects_bad_root(tmp_path: Path):
    assert scoped.main(["--check", "--project-root", str(tmp_path / "nope")]) == 2
    with pytest.raises(SystemExit):
        scoped.main(["--project-root", str(tmp_path)])        # --check 필수


# ── validate_ssot --project-root ─────────────────────────────────────────────

def _hash() -> str:
    h, why = validate_ssot._expected_source_hash()
    assert h, why
    return h


def test_generated_hash_drift_is_scoped(ws: Path, monkeypatch):
    _write(ws / GEN_A, f'SOURCE_HASH = "{_hash()}"\n')
    _write(ws / GEN_B, 'SOURCE_HASH = "0000000000000000"\n')
    monkeypatch.setattr(validate_ssot, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(validate_ssot, "GENERATED_TARGETS", [("python", GEN_A), ("python", GEN_B)])

    a = validate_ssot.load_scope(ws / "projects" / "repo_a", ws)
    b = validate_ssot.load_scope(ws / "projects" / "repo_b", ws)
    assert validate_ssot.check_generated_drift(a) == []
    assert any("repo_b" in v for v in validate_ssot.check_generated_drift(b))
    assert any("repo_b" in v for v in validate_ssot.check_generated_drift())


def _pin_repo(ws: Path, name: str, pin: str, source_hash: str) -> None:
    d = ws / "projects" / name
    _write(d / "pyproject.toml",
           f'dependencies = ["energy-contracts @ git+https://example.invalid/energy-contracts@{pin}"]\n')
    _write(d / "src" / "_generated_constants.py",
           f'SOURCE_HASH = "{source_hash}"\nSTRATEGY_CODES = ["M00"]\n')


def test_pin_lockstep_blocks_only_the_lagging_repo(ws: Path, monkeypatch):
    _pin_repo(ws, "repo_a", "v0.3.57", _hash())
    _pin_repo(ws, "repo_b", "v0.3.56", "0000000000000000")
    monkeypatch.setattr(validate_ssot, "WORKSPACE_ROOT", ws)
    monkeypatch.setattr(validate_ssot, "EC_PIN_CONSUMERS", ("repo_a", "repo_b"))
    blob = json.dumps({"properties": {"strategy": {"enum": ["M00"]}}})
    monkeypatch.setattr(validate_ssot, "_git_show_at_tag", lambda _tag, _path: (blob, ""))

    def scope(name: str):
        return validate_ssot.load_scope(ws / "projects" / name, ws)

    assert validate_ssot.check_ec_pin_lockstep(scope("repo_a")) == []
    vb = validate_ssot.check_ec_pin_lockstep(scope("repo_b"))
    assert any("v0.3.56" in v for v in vb), vb
    assert any("SOURCE_HASH" in v for v in vb), vb
    assert validate_ssot.check_ec_pin_lockstep(scope("repo_none")) == []
    assert len(validate_ssot.check_ec_pin_lockstep()) == 2    # 전수: pin 갈라짐 + hash 갈라짐


def test_e_code_emitter_check_is_scoped(ws: Path, capsys):
    import yaml
    sim = ws / "8.simulation"
    _repo(sim, {"reverse/configs/data_spec.yaml":
                yaml.safe_dump({"ems": {"e_labels": ["E14"], "e_to_m": {"E14": ["M02"]}}})})

    a = validate_ssot.load_scope(ws / "projects" / "repo_a", ws)
    s = validate_ssot.load_scope(sim, ws)
    assert validate_ssot.check_e_code_emitter_coverage(workspace_root=ws, scope=a) == []
    assert "범위 밖" in capsys.readouterr().out
    assert any("E14" in v for v in validate_ssot.check_e_code_emitter_coverage(workspace_root=ws, scope=s))
    assert any("E14" in v for v in validate_ssot.check_e_code_emitter_coverage(workspace_root=ws))


# ── 설치기가 쓰는 hook 본문 ───────────────────────────────────────────────────

def test_installed_hook_template_passes_project_root():
    text = (ROOT / "scripts" / "install_ssot_gate.sh").read_text(encoding="utf-8")
    hook = text.split("<<'HOOK'", 1)[1].split("\nHOOK\n", 1)[0]
    calls = [ln for ln in hook.splitlines()
             if re.search(r'python "\$\w+" --(check|pre-commit)', ln)]
    assert len(calls) == 2, calls
    assert all('--project-root "$REPO_TOP"' in ln for ln in calls), calls
    assert "gen_constants.py\" --check" not in hook and '$GENERATOR' not in hook
