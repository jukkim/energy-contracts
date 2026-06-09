"""Pydantic mirrors of critics dataclasses — FastAPI OpenAPI 노출용.

dataclasses (Critic / CriticResult / Verdict / GateVerdict / BatchDebateVerdict)
는 도메인 중립 SSOT 로직 캐리어. FastAPI 가 OpenAPI schema 자동 생성하려면
Pydantic 이 필요 — 이 모듈이 그 mirror 를 제공한다.

호출 패턴 (GB / be-3d FastAPI router):
    >>> from energy_contracts.critics import BatchDebateVerdictModel
    >>> @router.post("/debate/{event_id}", response_model=BatchDebateVerdictModel)
    ... async def debate(...): ...

사냥꾼 frontend HIGH (2026-05-27): dataclass 만으로는 OpenAPI 가 빈 dict.
이 모듈로 schema 가 자동 노출됨.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Violation(BaseModel):
    """단일 critic 위반 항목 — `rule` 은 필수, 그 외 critic 별 evidence 자유."""

    # critic 마다 위반 evidence 가 다르므로 extra 필드 허용
    model_config = ConfigDict(extra="allow")

    rule: str = Field(..., description="위반 룰 식별자 (예: 'nda_source_exposed').")


class CriticResultModel(BaseModel):
    """Critic 단일 평가 결과 — `CriticResult.to_dict()` 의 Pydantic mirror."""

    critic: str = Field(
        ...,
        description="critic 이름 (c_legal / c_carbon / c_safety / c_data).",
    )
    verdict: Literal["pass", "warn", "fail"] = Field(
        ..., description="평가 결과."
    )
    score: float = Field(..., ge=0.0, le=1.0, description="신뢰도 점수 [0, 1].")
    violations: list[Violation] = Field(
        default_factory=list,
        description="발견된 위반 항목 (verdict=pass 면 빈 리스트).",
    )
    notes: str = Field(default="", description="critic 진단 메모.")


class GateVerdictModel(BaseModel):
    """`CriticsGate.evaluate_dispatch()` 결과 — 실시간 dispatch 게이트."""

    decision: Literal["pass", "warn", "block"] = Field(
        ...,
        description="실시간 결정. block 시 호출자가 dispatch 차단해야 함.",
    )
    results: list[CriticResultModel] = Field(
        default_factory=list,
        description="3 종 Critic (Safety + Legal + Data) 결과.",
    )
    cache_hit: bool = Field(
        default=False,
        description="이전 동일 signature 평가 재사용 여부.",
    )


class BatchDebateVerdictModel(BaseModel):
    """`CriticsGate.evaluate_batch_debate()` 결과 — 사후 4 종 종합."""

    judge_decision: Literal["pass", "needs_review", "fail"] = Field(
        ..., description="종합 심판 결정."
    )
    realtime_results: list[CriticResultModel] = Field(
        default_factory=list,
        description="dispatch 시점 Critic 3 종 결과 (cache hit 가능).",
    )
    carbon_result: CriticResultModel | None = Field(
        default=None,
        description=(
            "Carbon Critic 결과. outcome 미주입 시 None — false-pass 방지 (M2)."
        ),
    )
    notes: str = Field(default="", description="처리 메타 (cache/skip 정보).")


class BatchDebateResponse(BatchDebateVerdictModel):
    """HTTP `/api/v1/dr/debate/{event_id}` 응답 — VerdictModel + 도메인 메타."""

    event_id: str = Field(..., description="DR 이벤트 식별자.")
    n_participating_venues: int = Field(
        default=0,
        ge=0,
        description="dispatch 에 참여한 venue 수 (GB DB 기준).",
    )
    source: Literal["gridbridge", "fallback_local"] | None = Field(
        default=None,
        description=(
            "결과 출처. 'gridbridge' = GB ground truth. "
            "'fallback_local' = be-3d 가 GB unreachable 시 자체 평가. "
            "GB 직접 호출 시 None."
        ),
    )


class CriticsBlockDetail(BaseModel):
    """HTTP 409 BLOCK 응답 detail 본문 — `fmt_block_detail()` 의 Pydantic mirror."""

    reason: Literal["critics_block"] = Field(default="critics_block")
    decision: Literal["block"] = Field(default="block")
    results: list[CriticResultModel] = Field(default_factory=list)
    remediation_key: str = Field(
        ...,
        description="frontend i18n catalog lookup key.",
    )
    remediation: str = Field(
        ...,
        description="i18n 미적용 클라이언트용 한국어 default 텍스트.",
    )


__all__ = [
    "Violation",
    "CriticResultModel",
    "GateVerdictModel",
    "BatchDebateVerdictModel",
    "BatchDebateResponse",
    "CriticsBlockDetail",
]
