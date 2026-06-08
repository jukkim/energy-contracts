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
        critical_rules: frozenset[str] | set[str] | None = None,
    ) -> CriticResult:
        """위반 목록 → verdict.

        - 0 건: PASS
        - `critical_rules` 에 속한 룰이 1 건이라도 있으면: 즉시 FAIL (룰별 차등 —
          물리 interlock 처럼 단건도 차단해야 하는 hard 룰용. 사냥꾼 라운드 M1.)
        - 그 외 `fail_threshold` 이상: FAIL
        - 그 외: WARN
        """
        n = len(violations)
        crit = critical_rules or frozenset()
        has_critical = any(v.get("rule") in crit for v in violations)
        if n == 0:
            verdict = Verdict.PASS
            score = 1.0
        elif has_critical or n >= fail_threshold:
            verdict = Verdict.FAIL
            score = max(0.0, 1.0 - 0.3 * n)
        else:
            verdict = Verdict.WARN
            score = max(0.0, 1.0 - 0.2 * n)
        return CriticResult(
            critic_name=self.name,
            verdict=verdict,
            score=score,
            violations=violations,
            notes=notes,
        )
