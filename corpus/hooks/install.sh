#!/bin/sh
# install.sh — 코퍼스 pre-push 훅을 소비 repo 에 설치한다(멱등).
#
#   sh corpus/hooks/install.sh                 # 알려진 소비 repo 전부
#   sh corpus/hooks/install.sh /path/to/repo   # 지정 repo
#
# 기존 pre-push 가 있으면 덮어쓰지 않고 **체인**한다(줄 하나 추가). 남의 훅을 지우지 않는다.
# ⚠ core.hooksPath 가 전역 훅으로 설정돼 있으면 per-repo 훅은 전역 forwarder 를 통해서만 불린다.
#   `~/.git-hooks-global/pre-push` 가 per-repo pre-push 로 위임하는지 확인할 것(myjob docs/GIT_HOOKS_GLOBAL.md).

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SRC="$HERE/pre_push_corpus.sh"
MARK="pre_push_corpus.sh"

PROJECTS=$(cd "$HERE/../../.." && pwd)     # …/myjob/projects
DEFAULT_REPOS="$PROJECTS/building-energy-3d
$PROJECTS/building-energy-3d-lab
$PROJECTS/energy-decision-studio
$PROJECTS/energy-contracts
$PROJECTS/../8.simulation"

REPOS=${*:-$DEFAULT_REPOS}

for repo in $REPOS; do
  [ -d "$repo/.git" ] || { echo "  ── skip (git repo 아님): $repo"; continue; }
  HOOK="$repo/.git/hooks/pre-push"
  if [ -f "$HOOK" ] && grep -q "$MARK" "$HOOK" 2>/dev/null; then
    echo "  ✅ 이미 설치됨: $(basename "$repo")"; continue
  fi
  if [ -f "$HOOK" ]; then                   # 기존 훅 보존 + 체인
    printf '\n# corpus 능력 검사 체인(2026-08-01)\nsh "%s" "$@" || exit $?\n' "$SRC" >> "$HOOK"
    echo "  ✅ 체인 추가: $(basename "$repo")"
  else
    printf '#!/bin/sh\nsh "%s" "$@" || exit $?\n' "$SRC" > "$HOOK"
    chmod +x "$HOOK" 2>/dev/null || true
    echo "  ✅ 신규 설치: $(basename "$repo")"
  fi
done
echo "완료. 우회는 SKIP_CORPUS_PREPUSH=1 git push"
