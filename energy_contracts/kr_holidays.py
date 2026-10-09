"""대한민국 관공서 공휴일표 접근 함수 — 자료 = ``data/kr_public_holidays.json`` (2026-10-10, 게이트웨이 E2 STUDIO-040 요청).

소비처(게이트웨이 프로파일 분해 등)는 표를 복사하지 않고 이 함수로 읽는다. 표가 다루는 해(:func:`coverage_years`) 밖의 날은
'공휴일 아님' 이 아니라 **못 잼**이다(:func:`covers` 로 먼저 확인한다).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

HOLIDAYS_PATH = Path(__file__).resolve().parent / "data" / "kr_public_holidays.json"
SOURCE_ID = "energy-contracts/data/kr_public_holidays.json"


@lru_cache(maxsize=1)
def document() -> dict[str, Any]:
    return json.loads(HOLIDAYS_PATH.read_text(encoding="utf-8"))


def coverage_years() -> tuple[int, int]:
    first, last = document()["coverage_years"]
    return int(first), int(last)


def covers(day: str) -> bool:
    """이 날(``YYYY-MM-DD``)의 해가 표 안인가."""
    first, last = coverage_years()
    return first <= int(str(day)[:4]) <= last


@lru_cache(maxsize=1)
def _by_date() -> dict[str, dict[str, Any]]:
    return {row["date"]: row for rows in document()["years"].values() for row in rows}


def holiday(day: str) -> dict[str, Any] | None:
    """공휴일이면 그 행(date·name_ko·kind), 아니면 None. 표 밖의 해면 KeyError(못 잼 — 아님으로 읽지 않는다)."""
    day = str(day)[:10]
    if not covers(day):
        raise KeyError(f"KR_HOLIDAY_YEAR_NOT_COVERED: {day[:4]} (표 {coverage_years()})")
    return _by_date().get(day)


def holidays_between(start: str, end: str) -> list[dict[str, Any]]:
    """[start, end] 안의 공휴일 행(날짜 순). 표 밖의 해가 섞이면 KeyError."""
    start, end = str(start)[:10], str(end)[:10]
    for y in range(int(start[:4]), int(end[:4]) + 1):
        if not covers(f"{y}-01-01"):
            raise KeyError(f"KR_HOLIDAY_YEAR_NOT_COVERED: {y} (표 {coverage_years()})")
    return [row for d, row in sorted(_by_date().items()) if start <= d <= end]
