"""C-Data — NDA 출처 fingerprint 노출 검출 (private-data-disclosure.md)."""

from __future__ import annotations

import re
from typing import Any

from .critic_base import Critic, CriticResult


NDA_SOURCE_PATTERNS = [
    (r"한수원", "KHNP"),
    (r"\bKHNP\b", "KHNP"),
    (r"hansuwon", "KHNP"),
    (r"\bIITP\b", "IITP"),
    (r"정보통신기획평가원", "IITP"),
    (r"레플러스", "REPLUS"),
    (r"\bREPLUS\b", "REPLUS"),
    (r"replus", "REPLUS"),
    (r"\bGS25\b", "convenience_store_private"),
    (r"T&M", "convenience_store_private"),
    (r"에너지엑스\s*BACnet", "energyx_private"),
]

NDA_FINGERPRINT_FILENAMES = [
    re.compile(r"hansuwon[_\-/.]"),
    re.compile(r"iitp[_\-/.]"),
    re.compile(r"replus[_\-/.]"),
    re.compile(r"khnp[_\-/.]"),
]

ANONYMIZED_OK_PATTERNS = [
    "비공개 한국 실측",
    "Anonymous Korean",
    "비공개 검증 셋",
    "Held-out Korean",
    "Site A",
    "Site B",
    "Site C",
    "private_set_",
]


class DataCritic(Critic):
    name = "c_data"

    def review(self, answer: str, context: dict[str, Any] | None = None) -> CriticResult:
        violations: list[dict[str, Any]] = []

        for pat, src in NDA_SOURCE_PATTERNS:
            if re.search(pat, answer, re.IGNORECASE):
                violations.append({
                    "rule": "nda_source_exposed",
                    "source": src,
                    "match_pattern": pat,
                    "remediation": "익명 표현으로 대체 (예: '비공개 한국 실측 데이터셋')",
                })

        for pat in NDA_FINGERPRINT_FILENAMES:
            if pat.search(answer.lower()):
                violations.append({
                    "rule": "nda_filename_pattern",
                    "pattern": pat.pattern,
                    "remediation": "파일명에서 출처명 제거 (private_set_X)",
                })

        if context and context.get("disclose_mode") == "public":
            for ok in ANONYMIZED_OK_PATTERNS:
                if ok in answer:
                    break
            else:
                if any("실측" in answer for _ in [0]):
                    violations.append({
                        "rule": "real_data_mentioned_without_anonymization",
                        "remediation": "외부 노출 시 익명화 표현 의무",
                    })

        return self._make_result(
            violations,
            fail_threshold=1,
            notes="private-data-disclosure.md — NDA 1 건만 노출돼도 FAIL",
        )

    def _make_result(self, violations, warn_threshold=1, fail_threshold=1, notes=""):
        from .critic_base import CriticResult, Verdict

        n = len(violations)
        if n == 0:
            return CriticResult(self.name, Verdict.PASS, 1.0, [], notes)
        return CriticResult(
            critic_name=self.name,
            verdict=Verdict.FAIL,
            score=0.0,
            violations=violations,
            notes=notes,
        )
