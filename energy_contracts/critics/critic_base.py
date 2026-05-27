"""Critic 추상 베이스 + 결과 형식.

Layer 2 Debate Arena 가 각 Critic 의 review() 호출 결과를 라운드 record 로 적재.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CriticResult:
    critic_name: str
    verdict: Verdict
    score: float
    violations: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "critic": self.critic_name,
            "verdict": self.verdict.value,
            "score": self.score,
            "violations": self.violations,
            "notes": self.notes,
        }


class Critic(ABC):
    name: str = "base"

    @abstractmethod
    def review(self, answer: str, context: dict[str, Any] | None = None) -> CriticResult:
        ...

    def _make_result(
        self,
        violations: list[dict[str, Any]],
        warn_threshold: int = 1,
        fail_threshold: int = 3,
        notes: str = "",
    ) -> CriticResult:
        n = len(violations)
        if n == 0:
            verdict = Verdict.PASS
            score = 1.0
        elif n < fail_threshold:
            verdict = Verdict.WARN
            score = max(0.0, 1.0 - 0.2 * n)
        else:
            verdict = Verdict.FAIL
            score = max(0.0, 1.0 - 0.3 * n)
        return CriticResult(
            critic_name=self.name,
            verdict=verdict,
            score=score,
            violations=violations,
            notes=notes,
        )
