#!/bin/sh
# pre_push_corpus.sh — 푸시 직전, 이번 변경이 건드린 능력만 자동 재검사.
#
# 왜 pre-push 인가: "수정 발생 시 전수 수행" 요구를 사람의 기억에 맡기지 않기 위해서다.
#   커밋마다 돌리기엔 무겁고(라이브 호출), CI 에만 두면 러너 장애 시 통째로 비는 걸
#   2026-08-01 에 실증했다(러너 17개 크래시 루프 → 필수 체크 미생성 → 머지 불가).
#
# 정책:
#   · 정적 드리프트(선언 불일치·A/C 커버리지 누락) = **차단**. 서비스 없이도 늘 판정 가능하다.
#   · 능력 회귀(GREEN→RED) = **차단**. 그래서 --baseline 을 반드시 넘긴다(없으면 판정 자체가 죽는다).
#   · 라이브 판정 불가(서비스 다운) = **정적 폴백 후 통과**. 판정 불가를 실패로 취급하면
#     --no-verify 습관만 만든다. 단 D층(정적)만은 반드시 통과시킨다.
#
# 2026-08-01 사냥꾼 라운드에서 고친 것 4:
#   ① 러너 탐색 경로 off-by-one → 8.simulation(게이트웨이 소유 repo)에서 **영구 무성 통과**였다.
#      미발견 시 조용히 exit 0 하던 것도 경고로 바꿨다("설치됨"인데 안 도는 상태가 안 보였다).
#   ② push ref(stdin) 무시 → 새 브랜치는 마지막 커밋만, **HEAD 아닌 브랜치 푸시는 검사 0건**.
#      git 이 stdin 으로 주는 <local ref> <local sha> <remote ref> <remote sha> 를 읽는다.
#   ③ --baseline 미전달 → regressions 가 항상 빈 배열(= 회귀 차단이 도달 불가 코드).
#   ④ 실행 흔적 0 → 사후에 "그 푸시 때 게이트가 돌았나"를 확인할 수 없었다. 저널 1줄 기록.
#
# 설치: sh corpus/hooks/install.sh
# 우회: SKIP_CORPUS_PREPUSH=1 git push   (권장 X — 저널에 bypass 로 남는다)

JOURNAL="$HOME/.corpus-gate.log"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
REPO_NAME=$(basename "$REPO_ROOT")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

_journal() {   # 시각 repo 브랜치 결과 파일수
  printf '%s %s %s %s files=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$REPO_NAME" "$BRANCH" "$1" "$2" \
    >> "$JOURNAL" 2>/dev/null
}

if [ -n "$SKIP_CORPUS_PREPUSH" ]; then
  _journal "bypass(SKIP_CORPUS_PREPUSH)" 0
  exit 0
fi

RUNNER=""
for cand in \
  "$REPO_ROOT/../energy-contracts/corpus/run_corpus.py" \
  "$REPO_ROOT/../projects/energy-contracts/corpus/run_corpus.py" \
  "$REPO_ROOT/corpus/run_corpus.py" \
  "$REPO_ROOT/../../projects/energy-contracts/corpus/run_corpus.py"
do
  [ -f "$cand" ] && RUNNER="$cand" && break
done
if [ -z "$RUNNER" ]; then
  # 조용한 통과 금지 — "설치됐는데 한 번도 안 돈다"가 가장 위험한 상태다.
  echo "⚠️  [corpus] 러너를 찾지 못했습니다($REPO_ROOT 기준). 능력 검사 없이 푸시합니다." >&2
  _journal "no-runner" 0
  exit 0
fi

# ── 검사 대상 파일 ─────────────────────────────────────────────────────────
#   git 은 stdin 으로 푸시되는 ref 를 준다. HEAD 만 보면 다른 브랜치 푸시를 통째로 놓친다.
FILES=""
while read -r _local_ref local_sha _remote_ref remote_sha; do
  [ -z "$local_sha" ] && continue
  case "$local_sha" in *[!0]*) ;; *) continue ;; esac      # 삭제 푸시(local=0…0)는 건너뜀
  case "$remote_sha" in
    *[!0]*) RANGE="$remote_sha..$local_sha" ;;             # 기존 브랜치 = 원격 이후 커밋만
    *)                                                      # 신규 브랜치 = 기본브랜치 분기점부터
      BASE=$(git merge-base "$local_sha" origin/HEAD 2>/dev/null \
             || git merge-base "$local_sha" origin/master 2>/dev/null \
             || git merge-base "$local_sha" origin/main 2>/dev/null)
      RANGE="${BASE:+$BASE..}$local_sha"
      [ -z "$BASE" ] && RANGE="$local_sha~1..$local_sha" ;;
  esac
  FILES="$FILES $(git diff --name-only "$RANGE" 2>/dev/null)"
done

# stdin 이 비어 있을 때(직접 실행·구 git)만 예전 방식으로 폴백.
if [ -z "$(printf '%s' "$FILES" | tr -d ' \n')" ]; then
  UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
  if [ -n "$UPSTREAM" ]; then
    FILES=$(git diff --name-only "$UPSTREAM"...HEAD 2>/dev/null)
  else
    FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
  fi
fi
FILES=$(printf '%s' "$FILES" | tr ' ' '\n' | sed '/^$/d' | sort -u)
NFILES=$(printf '%s\n' "$FILES" | sed '/^$/d' | wc -l | tr -d ' ')
[ "$NFILES" = "0" ] && { _journal "empty" 0; exit 0; }

# ── 검사 ──────────────────────────────────────────────────────────────────
#   --baseline 필수(없으면 회귀 판정이 죽는다). --report 는 금지 —
#   부분 스윕이 원장을 덮어써 신선도를 위조한다.
# shellcheck disable=SC2086
OUT=$(python "$RUNNER" --changed $FILES --baseline 2>&1)
RC=$?

# CI 러너 생사 대조(차단 아님·경고) — 러너가 죽어 있으면 이 푸시의 필수 체크가 영원히 pending 되고
#   admin 머지조차 막힌다(2026-08-01 실증).
VERIFY="$(dirname "$RUNNER")/../scripts/fix_gh_runners.py"
if [ -f "$VERIFY" ]; then
  python "$VERIFY" --verify --repo "$REPO_NAME" >/dev/null 2>&1 || {
    echo "⚠️  [runner] $REPO_NAME 의 self-hosted 러너 이상 — 이 푸시의 CI 가 안 돌 수 있습니다." >&2
    echo "   확인: python projects/energy-contracts/scripts/fix_gh_runners.py --verify" >&2
  }
fi

case "$RC" in
  0) _journal "pass" "$NFILES"; exit 0 ;;
  3)
    # 불완전 스윕(SKIP 과다). 훅은 --compose 를 주지 않으므로 B-op R층 SKIP 은 **설계상 정상**이다.
    #   차단하면 모든 푸시가 막힌다(2026-08-01 도입 직후 자기 푸시를 막아서 발견).
    #   신호는 살려두되(저널·stderr) 통과시킨다 — exit 3 의 소비자는 수동 --all 과 CI 다.
    echo "ℹ️  [corpus] 불완전 스윕(B-op R층은 --compose 필요) — 정적·라이브 검사는 통과." >&2
    _journal "incomplete(skip)" "$NFILES"; exit 0 ;;
  2)
    # 라이브 판정 불가 — 그래도 **정적(D층)은 반드시** 통과시킨다.
    #   게이트가 강할수록(라이브 매핑) 서비스 하나에 통째로 무력화되던 역설을 막는다.
    # ⚠ 예전엔 이 줄이 무조건 "서비스 다운" 이라고 단정했다. 2026-08-02 에 게이트웨이·
    #   5090 EXAONE 이 200 으로 멀쩡한데도 그렇게 보고해 사용자를 재기동 점검으로 보냈다.
    #   실제 원인은 429(RATE_LIMIT) 였다. 원인은 아래 UNKNOWN 사유 줄이 말한다.
    echo "⚠️  [corpus] 라이브 판정 불가(UNKNOWN 과다) — 정적 검사로 대체합니다." >&2
    echo "    원인은 아래 '❔ UNKNOWN 사유' 를 볼 것 — SERVICE_DOWN(정말 죽음)과" >&2
    echo "    RATE_LIMIT(살아서 429 = 우리 부하)은 조치가 다르다." >&2
    echo "$OUT" | tail -8 >&2
    if python "$RUNNER" --suite static >/dev/null 2>&1; then
      _journal "degraded-static-pass" "$NFILES"; exit 0
    fi
    echo "❌ [corpus] 정적 검사도 실패 — 푸시를 중단합니다." >&2
    python "$RUNNER" --suite static 2>&1 | tail -12 >&2
    _journal "degraded-static-fail" "$NFILES"; exit 1 ;;
  *)
    echo "❌ [corpus] 능력 검사 실패 — 푸시를 중단합니다." >&2
    echo "$OUT" | tail -25 >&2
    echo "   (정적 드리프트면 gen_corpus.py 재생성, 회귀면 원인 수정 후 재시도.)" >&2
    echo "   부득이한 경우: SKIP_CORPUS_PREPUSH=1 git push" >&2
    _journal "fail" "$NFILES"; exit 1 ;;
esac
