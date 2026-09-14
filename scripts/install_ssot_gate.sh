#!/bin/sh
# install_ssot_gate.sh — energy-contracts SSOT pin-lockstep 게이트 워크스페이스 설치기
#
# WHY (배경):
#   AI 챔피언 폴더는 단일 git 이 아니라 polyrepo(형제 repo)로 관리한다
#   (근거: myjob/docs/AI_CHAMPION_TRACKS.md "Git 관리 전략" — 배포 1repo=1배포 결합).
#   polyrepo 에서 SSOT 계약(energy-contracts)과 각 소비 repo 의 _generated_constants
#   를 동기 유지하는 pin-lockstep 게이트 = "소비 repo 의 pre-commit hook 이 형제
#   energy-contracts/scripts 로 올라가 drift 를 차단".
#
#   문제: 그 hook 은 각 repo 의 .git/hooks/ (로컬·비커밋)에만 존재 → fresh clone /
#   머신 B / 신규 소비 repo 에는 게이트가 없어 stale 상수 커밋이 무방비.
#   본 스크립트가 그 게이트를 워크스페이스 전 소비 repo 에 재현(idempotent)한다.
#
# ⛔ 범위 = 커밋하는 저장소 (2026-09-15):
#   예전 hook 은 범위 없이 `gen_constants.py --check` 를 돌렸다. 그 명령은 등록 소비처
#   **전부** 를 보므로 형제 체크아웃(8.simulation _shared) 하나의 drift 가 EC·be-3d·소비처
#   5곳의 무관한 커밋을 막았고 `--no-verify` 가 상습화됐다. 지금 hook 은
#   `--project-root "$(git rev-parse --show-toplevel)"` 로 **자기 저장소 소관만** 본다.
#   링크드 워크트리는 git common dir 로 같은 저장소로 판정한다(gen_constants_scoped.py).
#   전수 검사(CI·센티넬)는 여전히 인자 없는 `gen_constants.py --check`.
#
# USAGE (clone / 새 머신 / 신규 consumer 추가 / 이 파일 갱신 후):
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh gridbridge edge-agent  # 일부만
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh --force   # 남이 쓴 hook 도 덮어씀
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh --dry-run
#
# 설계:
#   - PROJECT_TARGETS(gen_constants.py)의 소비 repo 중 형제로 존재하는 것 + energy-contracts
#     자신에 설치. (EC 는 소관 생성본이 gcs_e_codes 투영뿐이다 — 형제 drift 로 안 막힌다.)
#   - building-energy-3d 는 자체 richer 설치기(scripts/install-pre-commit.sh,
#     정본 tools/hooks/pre-commit)를 보유 → 대상 외.
#   - **이 설치기가 쓴 hook**(헤더에 install_ssot_gate.sh) 은 매번 새로 쓴다 — 게이트 본문이
#     바뀌면 재실행 한 번으로 전부 갱신돼야 한다.
#   - 남이 쓴 hook 이 gen_constants 를 부르면 보존(--force 로만 교체). 범위 없는 옛 게이트면
#     [STALE] 로 알린다 — 그 hook 은 형제 drift 로 커밋을 막는다.
#   - 8sim-shared 는 별도 repo 루트(8.simulation) → 대상 외.

set -eu

FORCE=0
DRY=0
ONLY=""
for arg in "$@"; do
    case "$arg" in
        --force)   FORCE=1 ;;
        --dry-run) DRY=1 ;;
        -*) echo "unknown arg: $arg" >&2; exit 2 ;;
        *)  ONLY="$ONLY $arg" ;;
    esac
done

# projects/ 루트 = 이 스크립트(energy-contracts/scripts/) 기준 ../..
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 게이트 대상 (building-energy-3d 는 자체 설치기 → 별도 취급)
CONSUMERS="edge-agent gridbridge agentleague eduarena ingestion-worker"
CONTRACTS="energy-contracts"        # 계약 저장소 자신도 같은 게이트(자기 트리의 도구로 검사)
SELF_MANAGED="building-energy-3d"   # 자체 richer 설치기 보유

installed=0
skipped=0
missing=0

install_hook() {
    repo="$1"
    repo_dir="$PROJECTS_ROOT/$repo"

    if [ ! -d "$repo_dir/.git" ]; then
        echo "  [MISS] $repo — .git 없음(형제 clone 아님) → skip"
        missing=$((missing + 1))
        return
    fi

    hook_path="$repo_dir/.git/hooks/pre-commit"

    if [ "$FORCE" -eq 0 ] && [ -f "$hook_path" ] \
        && ! grep -q "install_ssot_gate.sh" "$hook_path" 2>/dev/null \
        && grep -q "gen_constants" "$hook_path" 2>/dev/null; then
        if grep -q -- "--project-root" "$hook_path" 2>/dev/null; then
            echo "  [KEEP] $repo — 남이 쓴 범위 게이트 hook 보존 (--force 로 덮어쓰기)"
        else
            echo "  [STALE] $repo — 남이 쓴 hook 이 **범위 없는** gen_constants 검사를 한다."
            echo "          형제 drift 로 커밋이 막힌다 → 확인 후 --force $repo 로 교체"
        fi
        skipped=$((skipped + 1))
        return
    fi

    if [ "$DRY" -eq 1 ]; then
        echo "  [DRY ] $repo — $hook_path 에 게이트 설치 예정"
        installed=$((installed + 1))
        return
    fi

    mkdir -p "$repo_dir/.git/hooks"
    cat > "$hook_path" <<'HOOK'
#!/bin/sh
# SSOT 검증 pre-commit hook — energy-contracts pin-lockstep 게이트
# 설치: energy-contracts/scripts/install_ssot_gate.sh (재실행으로 갱신 — 손편집 금지)
#
# 범위 = 커밋하는 저장소 (2026-09-15). 형제 체크아웃의 drift 로는 막지 않는다 —
#   그건 그 저장소의 커밋·CI 와 전수 점검(gen_constants.py --check) 몫이다.

REPO_TOP="$(git rev-parse --show-toplevel)"
SSOT_DIR="$(dirname "$0")/../../../energy-contracts/scripts"
# 커밋하는 저장소가 energy-contracts 자신이면 **그 작업 트리의** 도구로 검사한다
#   (메인 체크아웃의 사본이 워크트리 커밋을 판정하지 않게).
if [ -f "$REPO_TOP/scripts/gen_constants_scoped.py" ] && [ -d "$REPO_TOP/energy_contracts/schemas" ]; then
    SSOT_DIR="$REPO_TOP/scripts"
fi
VALIDATOR="$SSOT_DIR/validate_ssot.py"
SCOPED="$SSOT_DIR/gen_constants_scoped.py"

if [ ! -f "$VALIDATOR" ]; then
    echo "[SSOT pre-commit] ⚠ **못 잼** — validator 없음: $VALIDATOR (energy-contracts 미배치). 통과 아님"
elif [ ! -f "$SCOPED" ]; then
    echo "[SSOT pre-commit] ✗ energy-contracts 체크아웃이 낡았다 — 범위 검사기 없음: $SCOPED"
    echo "  git -C \"$SSOT_DIR/..\" pull --ff-only 후 재시도"
    exit 1
else
    # 1) 변경 파일 검사 (strategy + ports + schemas + 자기 저장소 generated/lockstep)
    if ! python "$VALIDATOR" --pre-commit --project-root "$REPO_TOP"; then
        echo ""
        echo "[SSOT pre-commit] 위반 발견 — 커밋 차단. 위 목록을 고친 뒤 재시도"
        exit 1
    fi
    # 2) 자기 저장소 _generated_constants 본문 전체 drift (SOURCE_HASH 헤더만으로는 우회 가능)
    if ! _ssot_out="$(python "$SCOPED" --check --project-root "$REPO_TOP" 2>&1)"; then
        echo "$_ssot_out"
        echo ""
        echo "[SSOT pre-commit] _generated_constants drift 발견 — 커밋 차단"
        echo "  'python projects/energy-contracts/scripts/gen_constants.py --all' 실행 후 재시도"
        exit 1
    fi
fi

# 3) pre-commit 프레임워크 위임 — 이 raw hook 이 .pre-commit-config.yaml 의
#    프레임워크 dispatcher 를 덮어썼을 때 그 hook 들(예: snapshot drift gate)을
#    보존하기 위해 SSOT 통과 후 위임. config·바이너리 없으면 조용히 skip.
if [ -n "$REPO_TOP" ] && [ -f "$REPO_TOP/.pre-commit-config.yaml" ] && command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --hook-stage pre-commit 2>/dev/null
    rc=$?
    if [ $rc -ne 0 ]; then
        echo ""
        echo "[pre-commit framework] hook 위반 — 커밋 차단 (.pre-commit-config.yaml)"
        exit 1
    fi
fi

exit 0
HOOK
    chmod +x "$hook_path"
    echo "  [OK  ] $repo — 게이트 설치 $hook_path"
    installed=$((installed + 1))
}

echo "[install_ssot_gate] projects 루트: $PROJECTS_ROOT"
echo "[install_ssot_gate] 게이트 설치 (force=$FORCE dry=$DRY only=${ONLY:-전체})"
for repo in $CONSUMERS $CONTRACTS; do
    if [ -n "$ONLY" ]; then
        case " $ONLY " in *" $repo "*) ;; *) continue ;; esac
    fi
    install_hook "$repo"
done

# 자체 관리 repo 안내 (덮어쓰지 않음)
for repo in $SELF_MANAGED; do
    if [ -d "$PROJECTS_ROOT/$repo/.git" ]; then
        echo "  [SELF] $repo — 자체 설치기 사용: sh $repo/scripts/install-pre-commit.sh"
    fi
done

echo "[install_ssot_gate] 완료: 설치 $installed · 보존 $skipped · 미존재 $missing"
