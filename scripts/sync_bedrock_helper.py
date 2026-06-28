"""Bedrock 헬퍼 SSOT → AI 챔피언 전 폴더 미러 동기화 (drift 가드).

SSOT = energy-contracts/energy_contracts/bedrock.py. 각 repo 는 vendored mirror 를 둔다
(repo 별 import path 이질 → 미러가 가장 robust; _generated_constants 미러 패턴과 동일).

  python energy-contracts/scripts/sync_bedrock_helper.py            # 동기화(쓰기)
  python energy-contracts/scripts/sync_bedrock_helper.py --check    # drift 검사(CI, 쓰기 없음)

키 값은 다루지 않는다(헬퍼 코드만). 키는 ~/.bedrock_api_key.txt(중앙) 또는 .env.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECTS = Path(__file__).resolve().parents[2]   # .../projects
_SSOT = _PROJECTS / "energy-contracts" / "energy_contracts" / "bedrock.py"

# repo 별 미러 경로 (구조 이질: backend/core vs src)
_MIRRORS = [
    "agentleague/backend/core/bedrock.py",
    "building-energy-3d/src/bedrock.py",
    "edge-agent/src/bedrock.py",
    "eduarena/backend/core/bedrock.py",
    "gridbridge/src/bedrock.py",
    "ingestion-worker/src/bedrock.py",
]
# 제외: 8.simulation/ems_transformer — 별 세션 소유(직접 수정 금지). 필요 시 자체 세션서 sync.

_HEADER = (
    "# ⚠ MIRROR — DO NOT EDIT. SSOT = energy-contracts/energy_contracts/bedrock.py\n"
    "#   동기화: python energy-contracts/scripts/sync_bedrock_helper.py\n"
    "#   키 출처: ~/.bedrock_api_key.txt (중앙) 또는 .env 의 BedrockAPIKey-5ir6\n\n"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="drift 검사만(쓰기 없음, CI)")
    a = ap.parse_args()
    if not _SSOT.exists():
        print(f"✗ SSOT 부재: {_SSOT}", file=sys.stderr)
        return 2
    content = _HEADER + _SSOT.read_text(encoding="utf-8")
    drift = 0
    for rel in _MIRRORS:
        dst = _PROJECTS / rel
        cur = dst.read_text(encoding="utf-8") if dst.exists() else None
        if cur == content:
            print(f"  ✓ {rel} (최신)")
            continue
        drift += 1
        if a.check:
            print(f"  ✗ DRIFT {rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            print(f"  ↻ synced {rel}")
    if a.check and drift:
        print(f"\n{drift} drift — sync 필요", file=sys.stderr)
        return 1
    print(f"\n{'drift 0' if a.check else f'{drift} synced'} · 미러 {len(_MIRRORS)}개")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
