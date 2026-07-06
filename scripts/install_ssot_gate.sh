#!/bin/sh
# install_ssot_gate.sh — energy-contracts SSOT pin-lockstep 게이트 워크스페이스 설치기
#
# WHY (배경):
#   AI 챔피언 폴더는 단일 git 이 아니라 polyrepo(형제 repo)로 관리한다
#   (근거: myjob/docs/AI_CHAMPION_TRACKS.md "Git 관리 전략" — 배포 1repo=1배포 결합).
#   polyrepo 에서 SSOT 계약(energy-contracts)과 각 소비 repo 의 _generated_constants
#   를 동기 유지하는 pin-lockstep 게이트 = "소비 repo 의 pre-commit hook 이 형제
#   energy-contracts/scripts 로 올라가 gen_constants.py --check 를 돌려 drift 차단".
#
#   문제: 그 hook 은 각 repo 의 .git/hooks/ (로컬·비커밋)에만 존재 → fresh clone /
#   머신 B / 신규 소비 repo 에는 게이트가 없어 stale 상수 커밋이 무방비.
#   본 스크립트가 그 게이트를 워크스페이스 전 소비 repo 에 재현(idempotent)한다.
#
# USAGE (clone / 새 머신 / 신규 consumer 추가 시):
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh --force   # richer hook 도 덮어씀
#   sh projects/energy-contracts/scripts/install_ssot_gate.sh --dry-run
#
# 설계:
#   - PROJECT_TARGETS(gen_constants.py)의 소비 repo 중 형제로 존재하는 것에 설치.
#   - building-energy-3d 는 자체 richer 설치기(scripts/install-pre-commit.sh,
#     agent snapshot gate 포함)를 보유 → 기본 skip (--force 로만 덮어씀).
#   - 기존 hook 이 이미 SSOT drift 검사(gen_constants 참조)를 포함하면 skip
#     (덮어써서 richer 게이트를 잃지 않도록).
#   - 8sim-shared 는 별도 repo 루트(8.simulation) → 대상 외.

set -eu

FORCE=0
DRY=0
for arg in "$@"; do
    case "$arg" in
        --force)   FORCE=1 ;;
        --dry-run) DRY=1 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

# projects/ 루트 = 이 스크립트(energy-contracts/scripts/) 기준 ../..
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 형제 소비 repo (building-energy-3d 는 자체 설치기 → 별도 취급)
CONSUMERS="edge-agent gridbridge agentleague eduarena ingestion-worker"
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

    # 이미 SSOT drift 게이트 포함 hook 이면 보존 (--force 아닌 한)
    if [ "$FORCE" -eq 0 ] && [ -f "$hook_path" ] && grep -q "gen_constants" "$hook_path" 2>/dev/null; then
        echo "  [KEEP] $repo — 기존 SSOT 게이트 hook 보존 (--force 로 덮어쓰기)"
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
# 설치: energy-contracts/scripts/install_ssot_gate.sh (재실행으로 갱신)
# 우회: git commit --no-verify (지양 — 정당한 사유 있을 때만)

VALIDATOR_DIR="$(dirname "$0")/../../../energy-contracts/scripts"
VALIDATOR="$VALIDATOR_DIR/validate_ssot.py"
GENERATOR="$VALIDATOR_DIR/gen_constants.py"

if [ ! -f "$VALIDATOR" ]; then
    echo "[SSOT pre-commit] validator 미존재: $VALIDATOR — 검사 스킵"
    exit 0
fi

# 1) 변경 파일만 검사 (strategy + ports + schemas + generated drift)
python "$VALIDATOR" --pre-commit
rc=$?
if [ $rc -ne 0 ]; then
    echo ""
    echo "[SSOT pre-commit] 위반 발견 — 커밋 차단"
    echo "  수정 후 재시도하거나 의도된 경우 'git commit --no-verify' 사용 (지양)"
    exit 1
fi

# 2) _generated_constants 본문 전체 drift 검사 (SOURCE_HASH 헤더만으로는 우회 가능)
if [ -f "$GENERATOR" ]; then
    python "$GENERATOR" --check >/dev/null 2>&1
    rc=$?
    if [ $rc -ne 0 ]; then
        echo ""
        echo "[SSOT pre-commit] _generated_constants drift 발견 — 커밋 차단"
        echo "  'python projects/energy-contracts/scripts/gen_constants.py --all' 실행 후 재시도"
        exit 1
    fi
fi

# 3) pre-commit 프레임워크 위임 — 이 raw hook 이 .pre-commit-config.yaml 의
#    프레임워크 dispatcher 를 덮어썼을 때 그 hook 들(예: snapshot drift gate)을
#    보존하기 위해 SSOT 통과 후 위임. config·바이너리 없으면 조용히 skip.
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null)"
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
echo "[install_ssot_gate] 소비 repo 게이트 설치 (force=$FORCE dry=$DRY)"
for repo in $CONSUMERS; do
    install_hook "$repo"
done

# 자체 관리 repo 안내 (덮어쓰지 않음)
for repo in $SELF_MANAGED; do
    if [ -d "$PROJECTS_ROOT/$repo/.git" ]; then
        echo "  [SELF] $repo — 자체 설치기 사용: sh $repo/scripts/install-pre-commit.sh"
    fi
done

echo "[install_ssot_gate] 완료: 설치 $installed · 보존 $skipped · 미존재 $missing"
