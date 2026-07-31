#!/bin/sh
# pre_push_corpus.sh — 푸시 직전, 이번 변경이 건드린 능력만 자동 재검사.
#
# 왜 pre-push 인가: "수정 발생 시 전수 수행" 요구를 사람의 기억에 맡기지 않기 위해서다.
#   커밋마다 돌리기엔 무겁고(라이브 호출), CI 에만 두면 러너 장애 시 통째로 비는 걸
#   2026-08-01 에 실증했다(러너 17개 크래시 루프 → 필수 체크 미생성 → 머지 불가).
#
# 정책(중요):
#   · 정적 드리프트(선언 불일치·A/C 커버리지 누락) = **차단**. 이건 서비스 없이도 늘 판정 가능하다.
#   · 라이브 판정 불가(서비스 다운·UNKNOWN 과다, run_corpus exit 2) = **경고 후 통과**.
#     판정 불가를 실패로 취급하면 --no-verify 습관만 만든다(절차서 §1.3 과 같은 원칙).
#   · 능력 회귀(GREEN→RED, exit 1) = **차단**. 잃어버린 능력은 푸시 전에 봐야 한다.
#
# 설치: sh corpus/hooks/install.sh <repo-path>...   (또는 인자 없이 = 알려진 소비 repo 전부)
# 우회: SKIP_CORPUS_PREPUSH=1 git push   (권장 X — 이유를 커밋 메시지에 남길 것)

[ -n "$SKIP_CORPUS_PREPUSH" ] && exit 0

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
RUNNER=""
for cand in \
  "$REPO_ROOT/../energy-contracts/corpus/run_corpus.py" \
  "$REPO_ROOT/corpus/run_corpus.py" \
  "$REPO_ROOT/../../projects/energy-contracts/corpus/run_corpus.py"
do
  [ -f "$cand" ] && RUNNER="$cand" && break
done
[ -z "$RUNNER" ] && exit 0        # 코퍼스가 없는 환경(단독 체크아웃) — 조용히 통과

# 이번 푸시에 포함되는 파일 목록. upstream 이 없으면(첫 푸시) 최근 커밋 기준.
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
if [ -n "$UPSTREAM" ]; then
  FILES=$(git diff --name-only "$UPSTREAM"...HEAD 2>/dev/null)
else
  FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
fi
[ -z "$FILES" ] && exit 0

# shellcheck disable=SC2086
OUT=$(python "$RUNNER" --changed $FILES 2>&1)
RC=$?

case "$RC" in
  0) exit 0 ;;
  2)
    echo "⚠️  [corpus] 라이브 판정 불가(서비스 다운·UNKNOWN 과다) — 푸시는 진행합니다." >&2
    echo "$OUT" | tail -12 >&2
    echo "   서비스 기동 후 확인: python $RUNNER --all --sweep full --report --baseline" >&2
    exit 0 ;;
  *)
    echo "❌ [corpus] 능력 검사 실패 — 푸시를 중단합니다." >&2
    echo "$OUT" | tail -25 >&2
    echo "   (정적 드리프트면 gen_corpus.py 재생성, 회귀면 원인 수정 후 재시도.)" >&2
    echo "   부득이한 경우: SKIP_CORPUS_PREPUSH=1 git push" >&2
    exit 1 ;;
esac
