"""Frontier 결정의 **재현 지문** (ADR-017).

## 무엇을 고정하고 무엇을 고정하지 않나

⚠ **LLM 이 같은 문장을 내놓게 만들지 않는다.** Frontier 생성은 비결정적일 수 있고,
그걸 결정론으로 바꾸려 들면 모델을 못 바꾸게 되거나 온도를 0 으로 묶어 품질을
잃는다. 결선에서 고정해야 하는 것은 생성이 아니라 **그 뒤**다:

    pinned candidate bundle  +  deterministic evaluator  +  selected PlanRevision

즉 **같은 후보 묶음을 같은 평가기에 넣으면 언제나 같은 결정이 나온다** 는 것을
해시로 못 박는다. 생성이 흔들리면 미리 고정한 replay bundle 로 갈아탄다.

## 왜 정규화가 먼저인가

후보 원문에는 **비결정 필드**가 섞인다 — 타임스탬프, trace id, 설명 문장의 순서.
그걸 그대로 해시하면 **같은 계획이 매번 다른 지문**이 되어 재현을 증명할 수 없다.
그래서 지문을 만들기 전에 반드시 정규화한다.

⚠ 반대 실수도 있다: 너무 많이 지우면 **다른 계획이 같은 지문**이 된다. 그래서
정규화는 "설명·시각·추적자" 만 걷어내고 **행위·대상·값은 하나도 안 건드린다.**
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

#: 평가기 판정 규칙이 바뀌면 **결정 지문도 바뀌어야 한다** — 안 바뀌면 옛 결정과
#: 새 결정이 같은 이름을 갖는다. 규칙을 고칠 때 이 값을 올린다.
EVALUATOR_VERSION = "1.0.0"

#: 후보에서 **걷어낼** 비결정 필드. 여기 없는 것은 지문에 들어간다.
#: ⚠ 늘릴 때 조심할 것 — 하나 늘릴 때마다 **서로 다른 계획이 같아질 위험**이 는다.
VOLATILE_FIELDS = frozenset({
    "created_at", "generated_at", "timestamp", "ts",
    "trace_id", "request_id", "run_id", "span_id",
    "latency_ms", "token_usage", "raw_text", "rationale", "explanation",
})


def _canon(v: Any) -> Any:
    """정규화 — 키 정렬 + 비결정 필드 제거. **값은 안 건드린다.**"""
    if isinstance(v, dict):
        return {k: _canon(v[k]) for k in sorted(v) if k not in VOLATILE_FIELDS}
    if isinstance(v, list):
        return [_canon(x) for x in v]
    return v


def _sha(obj: Any) -> str:
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def canonical_plan(draft: dict) -> dict:
    """PlanDraft → 정규 형태. 지문의 입력이자 **사람이 읽어 대조할 수 있는 형태**."""
    return _canon(draft)


def candidate_fingerprint(draft: dict) -> str:
    """후보 하나의 지문. 같은 계획이면 같고, 행위·대상·값이 다르면 다르다."""
    return "cand-" + _sha(canonical_plan(draft))[:32]


def generation_envelope(*, snapshot_id: str, objective_version: str,
                        policy_version: str, provider: str, model_id: str,
                        system_prompt: str, tool_schema: Any,
                        temperature: float, seed: int | None,
                        request_payload: Any) -> dict:
    """생성 조건을 **한 봉투**에 담는다.

    ⚠ 생성 결과가 아니라 **조건**이다. 같은 봉투인데 결과가 다르면 그건 모델의
    비결정성이고, 그 사실 자체가 기록돼야 한다 — 봉투를 안 남기면 "왜 달라졌나" 를
    영영 못 묻는다.
    """
    return {
        "snapshot_id": snapshot_id,
        "objective_version": objective_version,
        "policy_version": policy_version,
        "provider": provider,
        "model_id": model_id,
        "system_prompt_sha256": _sha(system_prompt),
        "tool_schema_sha256": _sha(_canon(tool_schema)),
        "temperature": temperature,
        "seed": seed,
        "request_payload_sha256": _sha(_canon(request_payload)),
    }


def decision_fingerprint(*, envelope: dict, candidates: list[dict],
                         selected_index: int,
                         evaluator_version: str = EVALUATOR_VERSION) -> dict:
    """**결정** 지문 — 같은 후보 묶음 + 같은 평가기 → 언제나 같은 값.

    후보 지문을 **정렬해서** 넣는다. 생성 순서가 흔들려도 같은 묶음이면 같은
    입력이어야 한다 — 순서까지 지문에 넣으면 모델이 순서를 바꿨다는 이유로
    "다른 결정" 이 된다.

    ⚠ 그런데 **무엇을 골랐는지는 순서와 무관하게 남겨야** 한다. 그래서 선택은
    인덱스가 아니라 **선택된 후보의 지문**으로 적는다 — 인덱스로 적으면 정렬
    뒤에 다른 후보를 가리키게 된다(실제로 처음에 그렇게 쓸 뻔했다).
    """
    if not candidates:
        raise ValueError("후보가 없다 — 결정 지문을 만들 수 없다")
    if not 0 <= selected_index < len(candidates):
        raise ValueError(f"selected_index 범위 밖: {selected_index}")
    cands = [candidate_fingerprint(c) for c in candidates]
    selected = cands[selected_index]
    payload = {
        "envelope": _canon(envelope),
        "candidates": sorted(cands),
        "evaluator_version": evaluator_version,
        "selected": selected,
    }
    return {
        "decision_fingerprint": "dec-" + _sha(payload)[:32],
        "selected_candidate_fingerprint": selected,
        "candidate_fingerprints": cands,
        "evaluator_version": evaluator_version,
    }
