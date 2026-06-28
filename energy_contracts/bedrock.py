"""AWS Bedrock Converse 클라이언트 — 팀 토큰 기반 경량 호출 헬퍼 (SSOT).

**이 파일이 워크스페이스 SSOT.** AI 챔피언 전 폴더가 본 헬퍼를 미러(vendored copy)로 공유한다.
미러 동기화: `python energy-contracts/scripts/sync_bedrock_helper.py` (drift 가드).

going-forward 정책(2026-06-24): Claude 가 본 프로젝트들에서 LLM 이 필요할 때(블라인드
LLM-judge 게이트, 코퍼스 검증, 데이터 합성 등) 이 헬퍼로 Bedrock 을 호출한다. 팀 토큰은
사용량·비용이 추적되므로 외부 유출 금지 — 키는 아래 _read_key 소스에서만 읽고, 코드/로그/
응답에 절대 노출하지 않는다(security-files 룰).

키 소스 우선순위(_read_key):
  1. 환경변수 `BedrockAPIKey-5ir6`
  2. **중앙 키 파일 `~/.bedrock_api_key.txt`** (runpod 선례와 동일 패턴 — 전 폴더 단일 출처)
  3. repo 로컬 `.env` (backend/.env, repo/.env)

호출 규약(인프라팀 안내):
  - Authorization: Bearer <ABSK 토큰>
  - 엔드포인트 model id 에 반드시 "us." 접두 (cross-region inference). 누락 시 HTTP 400.
  - Converse API: POST .../model/us.<modelId>/converse
  - Region 기본 us-east-1, **토큰 만료 2026-07-31**(갱신 필요).
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

_KEY_ENV_NAME = "BedrockAPIKey-5ir6"
_CENTRAL_KEY_FILE = Path.home() / ".bedrock_api_key.txt"   # 전 폴더 공유 단일 출처
_REGION = "us-east-1"

# 사용 가능 모델 (us. 접두는 호출 시 자동 결합)
MODELS = {
    "sonnet": "anthropic.claude-sonnet-4-6",
    "haiku": "anthropic.claude-haiku-4-5-20251001-v1:0",
    "opus": "anthropic.claude-opus-4-8",            # 팀 토큰 접근 가능(temperature 미지원)
    "opus-4-1": "anthropic.claude-opus-4-1-20250805-v1:0",
    "llama70b": "meta.llama3-3-70b-instruct-v1:0",
    "llama8b": "meta.llama3-1-8b-instruct-v1:0",
    "nova-pro": "amazon.nova-pro-v1:0",
}
DEFAULT_MODEL = "sonnet"

# temperature 파라미터를 거부하는 모델(Bedrock) — inferenceConfig 에서 생략
_NO_TEMPERATURE = {"anthropic.claude-opus-4-8"}


class BedrockError(RuntimeError):
    """Bedrock 호출 실패 — 메시지에 키 값은 절대 포함하지 않는다."""


def _read_key() -> str:
    """토큰을 env → 중앙파일 → repo .env 순으로 로드. 값은 반환만, 로깅 금지."""
    key = os.environ.get(_KEY_ENV_NAME)
    if key:
        return key.strip()
    # 중앙 키 파일(전 폴더 공유)
    if _CENTRAL_KEY_FILE.exists():
        val = _CENTRAL_KEY_FILE.read_text(encoding="utf-8").strip()
        if val:
            return val
    # repo 로컬 .env (정의된 필드만 매핑하는 pydantic 우회 직접 파싱)
    here = Path(__file__).resolve()
    candidates = [here.parents[1] / ".env", here.parents[2] / ".env",
                  Path.cwd() / ".env", Path.cwd() / "backend" / ".env"]
    for env_path in candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            name, val = line.split("=", 1)
            if name.strip() == _KEY_ENV_NAME:
                return val.strip().strip('"').strip("'")
    raise BedrockError(
        f"Bedrock 토큰 미설정 — {_CENTRAL_KEY_FILE} 또는 .env 에 {_KEY_ENV_NAME} 을(를) 추가하세요.")


def _post(prompt: str, model: str, system: str | None, max_tokens: int,
          temperature: float | None, timeout: float) -> dict:
    model_id = MODELS.get(model, model)
    url = f"https://bedrock-runtime.{_REGION}.amazonaws.com/model/us.{model_id}/converse"
    headers = {"Authorization": f"Bearer {_read_key()}", "Content-Type": "application/json"}
    infer: dict = {"maxTokens": max_tokens}
    if temperature is not None and model_id not in _NO_TEMPERATURE:
        infer["temperature"] = temperature
    body: dict = {"messages": [{"role": "user", "content": [{"text": prompt}]}],
                  "inferenceConfig": infer}
    if system:
        body["system"] = [{"text": system}]
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as exc:  # 네트워크 — 키 미포함 메시지
        raise BedrockError(f"Bedrock 네트워크 오류: {exc.__class__.__name__}") from None
    if resp.status_code != 200:  # resp.text 에 키 없음(요청 헤더에만) — 상태/사유만 표면화
        raise BedrockError(f"Bedrock 호출 실패 (HTTP {resp.status_code}): {resp.text[:300]}")
    return resp.json()


def converse(prompt: str, *, model: str = DEFAULT_MODEL, system: str | None = None,
             max_tokens: int = 512, temperature: float = 0.5, timeout: float = 60.0) -> str:
    """단일 user 프롬프트 → 어시스턴트 텍스트. model = MODELS 키 또는 raw modelId."""
    data = _post(prompt, model, system, max_tokens, temperature, timeout)
    return data["output"]["message"]["content"][0]["text"]


def converse_full(prompt: str, *, model: str = DEFAULT_MODEL, system: str | None = None,
                  max_tokens: int = 4096, temperature: float | None = None,
                  timeout: float = 180.0) -> dict:
    """converse + 토큰 usage(비용 회계). 반환 {"text","usage_in","usage_out"}."""
    data = _post(prompt, model, system, max_tokens, temperature, timeout)
    usage = data.get("usage", {})
    return {"text": data["output"]["message"]["content"][0]["text"],
            "usage_in": int(usage.get("inputTokens", 0)),
            "usage_out": int(usage.get("outputTokens", 0))}


def health() -> dict:
    """연결 스모크 — 키 값 비노출, 마스킹 메타만 반환."""
    key = _read_key()
    masked = f"{key[:4]}...{key[-3:]} ({len(key)}자)"
    reply = converse("연결 테스트입니다. '정상'이라고만 답하세요.",
                     model=DEFAULT_MODEL, max_tokens=20, temperature=0.0)
    return {"ok": True, "model": MODELS[DEFAULT_MODEL], "key": masked, "reply": reply.strip()[:60]}
