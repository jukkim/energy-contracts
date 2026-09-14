"""`gen_constants.py --check` 의 **저장소 범위** 판 — pre-commit 게이트 전용 (2026-09-15).

## 왜 있나

소비 저장소의 pre-commit 훅이 범위 없이 `gen_constants.py --check` 를 돌렸다. 그 명령은
`PROJECT_TARGETS` 의 **등록 소비처 전부** 를 보므로, building-energy-3d 커밋이 **형제**
체크아웃(8.simulation `_shared`)의 drift 로 막혔다. 막힌 쪽은 고칠 권한도 이유도 없으니
`--no-verify` 가 상습화됐다(2026-09-15 실측: EC·be-3d·8simulation 외 소비처 5곳).

규칙: **커밋 게이트는 커밋하는 저장소가 소유한 산출물만 본다.** 형제의 drift 는 그 형제의
커밋·CI·전수 점검(`gen_constants.py --check`, 인자 없음)이 잡는다.

## 왜 gen_constants.py 의 옵션이 아니라 별도 파일인가

`gen_constants.schemas_hash()` 는 **gen_constants.py 자기 바이트** 를 해시에 넣는다.
그 파일을 한 글자라도 고치면 등록 생성본 10개의 SOURCE_HASH 가 전부 바뀌어 모든 소비
저장소가 한꺼번에 drift 가 된다 — 게이트를 고치려다 게이트를 전부 빨갛게 만든다.
그래서 비교 로직은 gen_constants 의 공개 함수(load_schemas·gen_*·apply_exports_filter)를
그대로 import 해 쓰고, 이 파일은 **대상 선택** 만 더한다.

## 저장소 정체 = git common dir (경로 문자열이 아니다)

`PROJECT_TARGETS` 는 메인 체크아웃 경로(`projects/<repo>/…`)로 등록돼 있다. 링크드
워크트리(`projects/wt_<repo>_<topic>`)의 `--show-toplevel` 은 워크트리 경로라 문자열로는
절대 안 맞는다. 그래서 등록 경로의 소유 저장소와 `--project-root` 의 저장소를
`git rev-parse --git-common-dir` 로 대조하고, 같으면 **그 작업 트리 안의 같은 상대 경로**
(= 실제로 커밋되는 파일)를 비교한다.

사용법:
  python gen_constants_scoped.py --check --project-root "$(git rev-parse --show-toplevel)"

종료 코드: 0 통과(소관 대상 없음 포함) / 1 drift·누락 / 2 사용 오류
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_constants as gc  # noqa: E402

TAG = "[gen_constants_scoped]"


def clean_git_env() -> dict[str, str]:
    """상속된 GIT_* 제거 — 훅 안에서는 GIT_DIR·GIT_INDEX_FILE 이 export 돼 있어
    `git -C <다른 저장소>` 가 **커밋 중인 저장소** 를 답한다(validate_ssot 2026-06-18 실측과 같은 함정)."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _key(p: Path | str) -> str:
    return os.path.normcase(os.path.normpath(str(Path(p).resolve())))


@dataclass(frozen=True)
class RepoId:
    common_dir: str    # 비교용 정규화 키(Windows 에선 소문자) — 워크트리들이 공유하는 저장소 정체
    common_path: Path  # 원래 표기 그대로의 common dir — 이름을 읽을 때는 이걸 쓴다
    toplevel: Path     # 이 작업 트리의 루트(메인 체크아웃 또는 링크드 워크트리)


def repo_of(path: Path) -> RepoId | None:
    """`path`(존재하는 디렉토리)가 속한 git 저장소. git 이 없거나 저장소가 아니면 None."""
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--path-format=absolute",
             "--git-common-dir", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=clean_git_env(), timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = r.stdout.strip().splitlines()
    if r.returncode != 0 or len(lines) < 2:
        return None
    return RepoId(common_dir=_key(lines[0]), common_path=Path(lines[0]).resolve(),
                  toplevel=Path(lines[1]).resolve())


class Scope:
    """`project_root` 저장소가 소유한 워크스페이스 상대 경로만 통과시키는 필터."""

    def __init__(self, project_root: Path, workspace_root: Path | None = None) -> None:
        self.root = Path(project_root).resolve()
        self.workspace_root = Path(workspace_root or gc.WORKSPACE_ROOT).resolve()
        self.repo = repo_of(self.root)
        self._owners: dict[str, RepoId | None] = {}

    def _owner(self, probe: Path) -> RepoId | None:
        k = _key(probe)
        if k not in self._owners:
            self._owners[k] = repo_of(probe)
        return self._owners[k]

    def map(self, rel: str) -> Path | None:
        """등록 경로 `rel`(워크스페이스 상대)이 이 저장소 소관이면 **이 작업 트리 안의** 실제 경로.

        소유 저장소는 등록 경로의 가장 가까운 존재하는 조상으로 판정한다. 단 그 조상이
        저장소 폴더(`앞 2 단계`, validate_ssot.consumer_scan_roots 와 같은 관례)보다 위로
        올라가면 소유자를 모르는 것으로 본다 — 클론 안 된 형제가 워크스페이스(메타 저장소)
        소관으로 오판되지 않게.
        """
        registered = self.workspace_root / rel
        boundary = self.workspace_root.joinpath(*Path(rel).parts[:2])
        probe = registered.parent
        while not probe.exists() and probe != boundary and boundary in probe.parents:
            probe = probe.parent
        owner = self._owner(probe) if probe.exists() else None

        if self.repo is not None and owner is not None:
            if owner.common_dir != self.repo.common_dir:
                return None
            try:
                return self.repo.toplevel / registered.resolve().relative_to(owner.toplevel)
            except ValueError:
                return None
        # git 정체를 못 얻으면(저장소 아님·git 부재·형제 폴더 부재) 경로 포함으로만 판정한다.
        try:
            registered.resolve().relative_to(self.root)
        except ValueError:
            return None
        return registered

    def is_repo(self, directory: Path) -> bool:
        """`directory` 가 이 저장소(어느 작업 트리든)인가."""
        other = self._owner(Path(directory).resolve()) if Path(directory).exists() else None
        if self.repo is not None and other is not None:
            return other.common_dir == self.repo.common_dir
        return _key(directory) == _key(self.root)


Renderer = Callable[[str, str, dict], str]


def _default_renderer() -> Renderer:
    schemas = gc.load_schemas()
    full: dict[str, str] = {}

    def render(_project: str, lang: str, cfg: dict) -> str:
        if lang not in full:
            full[lang] = gc.gen_python(schemas) if lang == "python" else gc.gen_typescript(schemas)
        return gc.apply_exports_filter(full[lang], lang, cfg)

    return render


def check_scoped(project_root: Path, *,
                 targets: dict[str, dict] | None = None,
                 workspace_root: Path | None = None,
                 contracts_root: Path | None = None,
                 render: Renderer | None = None,
                 projection_drift: Callable[[], bool] | None = None) -> int:
    """`project_root` 저장소 소관 생성본만 `gen_constants.regenerate_all(check_only=True)` 와
    같은 기준(재생성 본문 전체 비교)으로 검사한다. 인자는 시험 주입용."""
    targets = gc.PROJECT_TARGETS if targets is None else targets
    scope = Scope(project_root, workspace_root)
    contracts_root = gc.CONTRACTS_ROOT if contracts_root is None else contracts_root

    selected: list[tuple[str, str, dict, str, Path]] = []
    out_of_scope = 0
    for proj, cfg in targets.items():
        for lang in ("python", "ts"):
            rel = cfg.get(lang)
            if not rel:
                continue
            path = scope.map(rel)
            if path is None:
                out_of_scope += 1
            else:
                selected.append((proj, lang, cfg, rel, path))

    # energy-contracts 자신이 소유한 생성물 = gcs_e_codes 투영(정본 legacy_ems_code_mapping 의 사본).
    owns_projection = scope.is_repo(contracts_root)
    if not selected and not owns_projection:
        print(f"{TAG} {scope.root} 소관 생성 대상 없음 — 검사할 것이 없다(대상 아님, 통과). "
              f"형제 {out_of_scope}개는 범위 밖")
        return 0

    drift = 0
    if owns_projection:
        check = projection_drift or (lambda: gc.legacy_e_codes.sync_projection(True))
        if check():
            print(f"{TAG} DRIFT: energy_contracts/schemas/ems_strategies.json"
                  "#default.legacy_mapping.gcs_e_codes (정본 투영)")
            drift += 1

    render = render or _default_renderer()
    for proj, lang, cfg, rel, path in selected:
        expected = render(proj, lang, cfg)
        if not path.exists():
            print(f"{TAG} MISSING: {path}  (등록 {rel})")
            drift += 1
        elif path.read_text(encoding="utf-8") != expected:
            print(f"{TAG} DRIFT: {path}  (등록 {rel})")
            drift += 1
        else:
            print(f"{TAG} OK:    {path}")

    print(f"{TAG} 소관 {len(selected)}개 검사 · drift {drift} · 형제 {out_of_scope}개 범위 밖"
          f"(전수 = gen_constants.py --check)")
    return 1 if drift else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="커밋하는 저장소가 소유한 _generated_constants 만 drift 검사 (pre-commit 용)")
    ap.add_argument("--check", action="store_true", required=True,
                    help="drift 검사 (쓰기 모드 없음 — 재생성은 gen_constants.py --all)")
    ap.add_argument("--project-root", type=Path, required=True,
                    help='커밋 중인 작업 트리 루트 — 보통 "$(git rev-parse --show-toplevel)"')
    args = ap.parse_args(argv)
    if not args.project_root.is_dir():
        print(f"{TAG} --project-root 가 디렉토리가 아니다: {args.project_root}")
        return 2
    return check_scoped(args.project_root)


if __name__ == "__main__":
    sys.exit(main())
