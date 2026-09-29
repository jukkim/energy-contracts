"""bump_ec_pin 의 소비자 잠금 파일 처리 — 막아야 할 것과 통과시킬 것 양쪽 (2026-09-29).

배경: airos-energy-decision 은 EC 를 `contracts/energy_contracts.lock.json`(커밋 + 스키마별 sha256)으로 고정한다.
bump_ec_pin 은 그 파일을 몰라, v0.3.62 bump 뒤에도 잠금이 v0.3.60 에 남아 AIROS SSOT Drift Check 가 빨갛게 됐다
(run 36554706022). 이 시험은 소비자 저장소 모양을 임시 폴더에 만들고 **이 EC 저장소의 HEAD** 를 목표로 삼는다
(CI 의 얕은 clone 에도 HEAD 는 있다 — 태그에 기대지 않는다).

해시 함수는 도구가 **소비자 모듈에서 불러 쓴다**. 가짜 소비자에는 일부러 EC 쪽 어떤 구현과도 다른 해시를 두어,
도구가 자기 사본이 아니라 소비자의 `pin_hash` 를 부르는지 확인한다.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import textwrap

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("_consumer_lock", _ROOT / "scripts" / "_consumer_lock.py")
assert _SPEC and _SPEC.loader
lock_tool = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(lock_tool)

SCHEMAS = ("energy_constants.json", "region_codes.json")

#: 소비자 해시 모듈(가짜) — 줄끝 정규화 + 소비자만의 접두사. EC 어디에도 이 구현은 없다.
_FAKE_CLIENT = textwrap.dedent('''
    import hashlib
    HASH_BASIS = "sha256(lf_normalised_bytes)"
    def pin_hash(raw: bytes) -> str:
        return "fake256:" + hashlib.sha256(raw.replace(b"\\r\\n", b"\\n")).hexdigest()
''')


def _fake_hash(raw: bytes) -> str:
    return "fake256:" + hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _head() -> str:
    return subprocess.run(["git", "-C", str(_ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def _blob(commit: str, name: str) -> bytes:
    return subprocess.run(["git", "-C", str(_ROOT), "show", f"{commit}:energy_contracts/schemas/{name}"],
                          capture_output=True, check=True).stdout


def _consumer(tmp_path: pathlib.Path, lock: dict, *, crlf: bool = False) -> pathlib.Path:
    projects = tmp_path / "projects"
    repo = projects / "fake-consumer"
    (repo / "src" / "fake_pkg").mkdir(parents=True)
    (repo / "src" / "fake_pkg" / "contracts_client.py").write_text(_FAKE_CLIENT, encoding="utf-8")
    (repo / "contracts").mkdir()
    text = json.dumps(lock, indent=2, ensure_ascii=False) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    (repo / "contracts" / "energy_contracts.lock.json").write_bytes(text.encode("utf-8"))
    return projects


def _fresh_lock(commit: str) -> dict:
    return {
        "repository": "https://github.com/jukkim/energy-contracts.git",
        "commit": commit,
        "hash_basis": "sha256(lf_normalised_bytes)",
        "note": "한글 설명은 그대로 남는다",
        "schemas": {name: _fake_hash(_blob(commit, name)) for name in SCHEMAS},
    }


# ── --check: 막아야 할 것 ────────────────────────────────────────────────────────────────────────

def test_stale_commit_is_reported(tmp_path, capsys) -> None:
    head = _head()
    stale = {**_fresh_lock(head), "commit": "0" * 40}
    n, bad = lock_tool.check(_ROOT, _consumer(tmp_path, stale), head)
    assert (n, bad) == (1, 1)
    assert "commit 0000000" in capsys.readouterr().out


def test_stale_schema_hash_is_reported(tmp_path, capsys) -> None:
    head = _head()
    stale = _fresh_lock(head)
    stale["schemas"]["region_codes.json"] = "fake256:" + "0" * 64
    n, bad = lock_tool.check(_ROOT, _consumer(tmp_path, stale), head)
    assert (n, bad) == (1, 1)
    assert "region_codes.json 해시 불일치" in capsys.readouterr().out


def test_a_different_hash_basis_is_refused_not_rewritten(tmp_path) -> None:
    head = _head()
    other = {**_fresh_lock(head), "hash_basis": "sha256(raw_bytes)"}
    projects = _consumer(tmp_path, other)
    assert lock_tool.check(_ROOT, projects, head) == (1, 1)
    with pytest.raises(lock_tool.LockError):
        lock_tool.bump(_ROOT, projects, head)


def test_a_schema_missing_at_the_target_is_refused_not_dropped(tmp_path) -> None:
    head = _head()
    lock = _fresh_lock(head)
    lock["schemas"]["no_such_schema.json"] = "fake256:" + "0" * 64
    projects = _consumer(tmp_path, lock)
    assert lock_tool.check(_ROOT, projects, head) == (1, 1)
    before = (projects / "fake-consumer" / "contracts" / "energy_contracts.lock.json").read_bytes()
    with pytest.raises(lock_tool.LockError):
        lock_tool.bump(_ROOT, projects, head)
    after = (projects / "fake-consumer" / "contracts" / "energy_contracts.lock.json").read_bytes()
    assert after == before                                    # 반쯤 쓰지 않는다


def test_no_single_target_is_unmeasured_not_pass(tmp_path) -> None:
    projects = _consumer(tmp_path, _fresh_lock(_head()))
    assert lock_tool.check(_ROOT, projects, None) == (1, 1)


# ── --check: 통과시킬 것 ─────────────────────────────────────────────────────────────────────────

def test_fresh_lock_passes(tmp_path) -> None:
    head = _head()
    assert lock_tool.check(_ROOT, _consumer(tmp_path, _fresh_lock(head)), head) == (1, 0)


def test_the_check_really_inspected_a_lock(tmp_path) -> None:
    """검사 0 건은 통과가 아니다 — 잠금을 찾았는지 센다."""
    assert lock_tool.consumer_locks(_consumer(tmp_path, _fresh_lock(_head())))
    assert lock_tool.check(_ROOT, tmp_path / "empty", _head()) == (0, 0)


# ── bump: 고치고, 고친 것이 --check 를 통과한다 ──────────────────────────────────────────────────

@pytest.mark.parametrize("crlf", [False, True])
def test_bump_turns_a_stale_lock_fresh_keeping_shape(tmp_path, crlf) -> None:
    head = _head()
    fresh = _fresh_lock(head)
    stale = {**fresh, "commit": "1" * 40, "branch": "old-branch",
             "schema_commits": {"region_codes.json": "2" * 40},
             "schemas": {name: "fake256:" + "0" * 64 for name in SCHEMAS}}
    projects = _consumer(tmp_path, stale, crlf=crlf)
    assert lock_tool.check(_ROOT, projects, head) == (1, 1)

    assert lock_tool.bump(_ROOT, projects, head) == ["fake-consumer"]
    raw = (projects / "fake-consumer" / "contracts" / "energy_contracts.lock.json").read_bytes()
    assert (b"\r\n" in raw) is crlf                              # 줄끝 보존
    got = json.loads(raw.decode("utf-8"))
    assert got == fresh                                          # 옛 branch·schema_commits 는 지워진다
    assert list(got) == list(fresh)                              # 칸 순서 그대로
    assert list(got["schemas"]) == list(SCHEMAS)                 # 스키마 집합·순서 그대로
    assert got["note"] == "한글 설명은 그대로 남는다"
    assert lock_tool.check(_ROOT, projects, head) == (1, 0)
    assert lock_tool.bump(_ROOT, projects, head) == []           # 두 번째는 무변경


def test_the_hash_is_the_consumers_function(tmp_path) -> None:
    """도구가 쓰는 해시는 소비자 모듈의 pin_hash 다 — 같은 파일에서 온 함수이고 결과가 같다."""
    projects = _consumer(tmp_path, _fresh_lock(_head()))
    hasher, basis, path = lock_tool.load_hasher(projects / "fake-consumer")
    assert path == projects / "fake-consumer" / "src" / "fake_pkg" / "contracts_client.py"
    assert hasher.__code__.co_filename == str(path)
    assert basis == "sha256(lf_normalised_bytes)"
    lf = b'{\n  "a": 1\n}\n'
    assert hasher(lf) == hasher(lf.replace(b"\n", b"\r\n")) == _fake_hash(lf)
    assert hasher(lf) != hasher(b'{\n  "a": 2\n}\n')


# ── 실제 워크스페이스(airos-energy-decision 체크아웃이 있을 때만) ─────────────────────────────────

_AIROS = _ROOT.parents[0] / "airos-energy-decision"


@pytest.mark.skipif(not (_AIROS / "contracts" / "energy_contracts.lock.json").is_file(),
                    reason="airos-energy-decision 형제 체크아웃이 없다(EC 단독 CI clone) — 합성 시험이 대신 본다")
def test_airos_hasher_is_airos_pin_hash_and_its_lock_is_self_consistent() -> None:
    """AIROS 의 `contracts_client.pin_hash` 와 도구가 부르는 함수가 같은 파일·같은 결과이고,
    AIROS 잠금은 자기 커밋에서 도구가 다시 계산한 것과 바이트 단위로 같다(AIROS 시험·verify_governance 와 같은 답)."""
    hasher, basis, path = lock_tool.load_hasher(_AIROS)
    assert path == _AIROS / "src" / "airos_energy_decision" / "contracts_client.py"
    spec = importlib.util.spec_from_file_location("_airos_cc_direct", path)
    assert spec and spec.loader
    direct = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(direct)
    assert hasher.__code__.co_code == direct.pin_hash.__code__.co_code
    assert basis == direct.HASH_BASIS
    samples = [b"", b'{\n  "x": 1\n}\n', b'{\r\n  "x": 1\r\n}\r\n', "한글".encode("utf-8")]
    assert [hasher(s) for s in samples] == [direct.pin_hash(s) for s in samples]

    raw = (_AIROS / "contracts" / "energy_contracts.lock.json").read_text(encoding="utf-8")
    lock = json.loads(raw)
    want = lock_tool.expected_lock(lock, _ROOT, lock["commit"], hasher, basis)
    assert want["schemas"] == lock["schemas"]
    assert lock_tool.render(want) == raw.replace("\r\n", "\n")
