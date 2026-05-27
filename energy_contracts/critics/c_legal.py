"""C-Legal — 법령 인용 정확성 (rules/legal-citation.md 기반 룰)."""

from __future__ import annotations

import re
from typing import Any

from .critic_base import Critic, CriticResult


DEPRECATED_TERMS = {
    "BEEC": "ZEB 인증으로 통합됨 (2025.1.1)",
    "건물에너지효율인증": "ZEB 인증으로 통합됨 (2025.1.1)",
    "그린리모델링 민간 이자지원": "2023 종료",
}

FUTURE_LAWS_REQUIRING_QUALIFIER = {
    "목표 에너지원단위": "2027 시행 예정 (확정 아님)",
}

UNVERIFIABLE_ARTICLE_PATTERN = re.compile(
    r"(건축법|녹색건축법|에너지이용합리화법|건축물의 에너지절약설계기준)\s*제\s*\d+\s*조"
    r"(?!\s*\([^)]+\))"
)

STATISTIC_WITH_ARTICLE_PATTERN = re.compile(
    r"제\s*\d+\s*조[에에는]*\s*(따[라르]|의[거하]).{0,30}\d+(\.\d+)?\s*%"
)


class LegalCritic(Critic):
    name = "c_legal"

    def review(self, answer: str, context: dict[str, Any] | None = None) -> CriticResult:
        violations: list[dict[str, Any]] = []

        for term, reason in DEPRECATED_TERMS.items():
            if term in answer:
                violations.append({
                    "rule": "deprecated_term",
                    "term": term,
                    "reason": reason,
                })

        for term, reason in FUTURE_LAWS_REQUIRING_QUALIFIER.items():
            if term in answer and "예정" not in answer and "시행 예정" not in answer:
                violations.append({
                    "rule": "future_law_missing_qualifier",
                    "term": term,
                    "reason": reason,
                })

        for m in UNVERIFIABLE_ARTICLE_PATTERN.finditer(answer):
            violations.append({
                "rule": "article_without_clause_name",
                "match": m.group(0),
                "reason": "조항 번호만 인용 — 조문명 동반 필수",
            })

        if STATISTIC_WITH_ARTICLE_PATTERN.search(answer):
            violations.append({
                "rule": "stat_article_combined",
                "reason": "통계 + 조항 결합 금지 (legal-citation.md)",
            })

        return self._make_result(violations, notes="legal-citation.md 룰셋 적용")
