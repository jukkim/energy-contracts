"""집계값에 **어디까지 실측인지**를 붙여 내보낸다 — AIRO 출력 계약 (등재 #27).

## ⛔ 이 파일은 **정본**이다. 소비 저장소의 사본을 고치지 마라

    정본  projects/energy-contracts/energy_contracts/provenance/envelope.py
    사본  8.simulation/ems_transformer/serving/_provenance_envelope.py
          projects/building-energy-3d/src/shared/provenance_envelope.py

사본은 **바이트 동일**해야 하고 `scripts/verify_provenance_vendors.py` 가 해시로
대조한다(각 저장소 pre-commit 에 걸려 있다). 왜 import 가 아니라 사본인가 —
저장소마다 `energy_contracts` **설치본 버전이 다르다**(2026-09-04 실측: 워크스페이스
소스 0.3.50 ↔ be-3d 설치본 0.3.46). import 로 두면 낡은 설치본에서 계약이 조용히
사라지고, 그러면 봉투 없이 나가는 경로가 다시 생긴다. 사본 + 해시 게이트가
「guarded mirror + verify_*_mirror」(전역 SSOT 룰)의 파이썬 판이다.

## 왜 이 계약이 있나

합계 하나만 내보내면 소비자는 그것이 **얼마나 실측인지 알 방법이 없다.**
이 워크스페이스가 반복해 밟은 함정이 그것이다:

  · 커버리지를 한 칸으로 세어 **30% ↔ 97%** 가 갈렸다(전역 룰 「"없음" 은 한 가지가
    아니다」의 발단)
  · 건물 합계를 **전 부문** 공표 총계와 비교해 MAPE 가 부풀린 분모로 좋아 보였다
    (be-3d `docs/RESIDUAL_DECOMPOSITION_2026-09-03.md`, 시군구 52.2% → 99.7%)

## ⛔ 첫 판은 5개 방어가 **전부** 뚫렸다 (사냥꾼 2차 팀B)

    잔차 1e-5 를 적어 두면 100 → 1,000,000,000 (1e7 배) 스케일이 통과
    reconciled_total 에 raw 를 **복사**하면 "화해했다"(reconciled=True) 로 기록
    허위 coverage 600 한 줄로 scope 600 이동이 통과
    `{"contract": "...v1"}` 맨 dict 가 assert_quotable 통과
    counts 에 NaN 을 넣으면 모든 비중이 NaN 이 되어 결손 검사가 통째로 무력

근본 원인 셋이었고 이 판은 그 셋을 정면으로 막는다:

1. **항등식을 안 셌다** → `sum(residual) ≈ reconciled − raw` 를 **강제**한다.
   잔차는 "적었나" 가 아니라 **차이를 설명하는가** 로 검사한다.
2. **요약을 검증하고 원장을 안 봤다** → 게이트는 반올림된 `*_pct` 가 아니라
   **`counts` 원장**을 본다.
3. **위조 가능한 맨 dict 였다** → 봉투는 `Envelope` 인스턴스이고, `assert_quotable`
   은 **타입으로** 생성 경로를 요구한다. 사후 변조도 재검산으로 잡는다.

## 봉투가 하는 일과 **하지 않는 일**

⚠ 봉투는 **산술 일관성만** 강제한다. `measured` 라고 적은 값이 정말 실측인지는
   **집계 코드의 책임**이다. 봉투를 통과했다는 것이 라벨이 참이라는 뜻은 아니다.
"""
from __future__ import annotations

import importlib.util as _ilu
import json as _json
import math
from dataclasses import dataclass, field
from pathlib import Path as _Path
from types import MappingProxyType
from typing import Any, Mapping


def _load_taxonomy() -> tuple[tuple, tuple, tuple]:
    """계보 taxonomy 를 **정본에서 가져온다** — 손으로 적지 않는다.

    ⛔ 한때 여기에 리터럴을 적어 taxonomy 가 **네 벌**이 됐다(정본 7종 / DB 2종 /
    화면 4종 / 봉투 6종). 화해 결과가 **축 분리**다(2026-09-03 사용자 결정 B):

        DataSource   값이 있고 **어디서 왔나** (measured…imputed)
        AbsenceKind  값이 **왜 없나** (not_applicable · missing · unknown)

    같은 enum 에 섞으면 "출처가 missing" 같은 말이 문법상 가능해진다.

    ⚠ 이 파일은 세 저장소에 사본으로 놓이므로 **패키지 이름으로 import 하지 않는다**
    (`_shared` 인 곳도, `src.shared` 인 곳도 있다). 조상 디렉터리를 올라가며
    생성본 **파일**을 찾아 경로로 로드하고, 없으면 정본 스키마 JSON 을 직접 읽는다.
    셋 다 실패하면 **예외를 던진다** — 리터럴 폴백을 두면 그 순간 다섯 번째 목록이
    생긴다.
    """
    here = _Path(__file__).resolve()
    rels_const = ("_shared/_generated_constants.py", "shared/_generated_constants.py",
                  "src/shared/_generated_constants.py")
    rels_schema = ("energy_contracts/schemas/data_classification.json",
                   "schemas/data_classification.json",
                   "projects/energy-contracts/energy_contracts/schemas/"
                   "data_classification.json")
    for anc in (here, *here.parents):
        for rel in rels_const:
            p = anc / rel
            if not p.is_file():
                continue
            spec = _ilu.spec_from_file_location(f"_prov_const_{abs(hash(str(p)))}", p)
            if spec is None or spec.loader is None:            # pragma: no cover
                continue
            m = _ilu.module_from_spec(spec)
            spec.loader.exec_module(m)
            if all(hasattr(m, a) for a in ("DATA_SOURCE_LABELS", "ABSENCE_KINDS",
                                           "ABSENCE_IN_DENOMINATOR")):
                return (tuple(m.DATA_SOURCE_LABELS), tuple(m.ABSENCE_KINDS),
                        tuple(m.ABSENCE_IN_DENOMINATOR))
        for rel in rels_schema:
            p = anc / rel
            if not p.is_file():
                continue
            d = _json.loads(p.read_text(encoding="utf-8"))
            defs = d.get("$defs") or {}
            src = tuple((defs.get("DataSource") or {}).get("enum") or ())
            ab = tuple((defs.get("AbsenceKind") or {}).get("enum") or ())
            absence = (d.get("default") or {}).get("absence") or {}
            den = tuple(k for k, v in absence.items() if v.get("in_denominator"))
            if src and ab and den:
                return src, ab, den
    raise ImportError(
        "계보 taxonomy 정본을 못 찾았다 — 생성본(`_generated_constants.py`)도 "
        "스키마(`data_classification.json`)도 조상 경로에 없다. "
        "리터럴로 때우지 마라(그 순간 목록이 한 벌 더 생긴다)")


DATA_SOURCE_LABELS, ABSENCE_KINDS, ABSENCE_IN_DENOMINATOR = _load_taxonomy()

#: 이 봉투가 실제로 다루는 출처 4종 — 정본 9종의 **부분집합**이며 정본에 없는
#  이름은 쓰지 않는다(교집합으로 강제한다 → 정본이 바뀌면 여기서 빨개진다).
_SOURCES_USED = ("measured", "certified", "calibrated", "imputed",
                 "simulated", "predicted")
_unknown_src = [k for k in _SOURCES_USED if k not in DATA_SOURCE_LABELS]
if _unknown_src:                                                     # pragma: no cover
    raise ImportError(
        f"정본 DataSource 에 없는 출처를 쓰려 한다: {_unknown_src} — "
        f"energy-contracts 스키마를 먼저 고쳐라(정본={list(DATA_SOURCE_LABELS)})")

#: 값의 계보 = 출처축 + 부재축. **부재는 값이 아니다**.
LINEAGE = _SOURCES_USED + tuple(ABSENCE_KINDS)
#: 합계에 실제로 들어가는 계보 — 부재는 제외된다.
CONTRIBUTING = _SOURCES_USED
#: **실측이 아닌** 계보 — 하나라도 있으면 "실측" 이라고 부르면 안 된다.
#  ⚠ `calibrated` 가 여기 있다: 실측에 맞춰 보정한 값은 실측이 아니다(팀B M-11).
NOT_MEASURED = tuple(k for k in _SOURCES_USED if k != "measured")
#: 잔차 갈래. `scope` 는 **배분 대상이 아니다**(건물이 아닌 몫).
RESIDUAL_KINDS = ("coverage", "scope", "quality", "unallocated")

#: 상대 허용오차. ⚠ 절대값이면 작은 단위에서 1000배 스케일이 무료로 통과한다(팀B M-9).
_REL_TOL = 1e-9
_ABS_FLOOR = 1e-9
#: ⛔ 잔차가 총계의 이 배수를 넘으면 장부가 값을 설명하지 못하는 것이다
#  (사냥꾼 3차 H-5: `quality=1e17` 이 총계 12,345 옆에 적혀 나갔다).
_RESIDUAL_MAX_RATIO = 10.0


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=_REL_TOL, abs_tol=_ABS_FLOOR)


class ProvenanceError(ValueError):
    """계약 위반 — **조용히 고치지 않는다.** 고치면 그 순간 감사 불가능해진다."""


def _num(x: Any, name: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ProvenanceError(f"{name}: 숫자가 아니다 ({x!r})")
    v = float(x)
    #: ⛔ NaN·inf 를 통과시키면 이후 **모든 비교가 False** 가 되어 게이트가 통째로
    #  무력해진다(팀B H-6: `missing_pct > 0` 이 NaN 에 대해 항상 False).
    if not math.isfinite(v):
        raise ProvenanceError(f"{name}: 유한한 수가 아니다 ({v!r}) — 검사를 무력화한다")
    return v


def _check_invariants(*, raw: float, rec: float | None, counts: Mapping[str, float],
                      resid: Mapping[str, float]) -> None:
    """봉투가 **참이어야 하는 것 전부**. 생성·검증 양쪽이 이 함수 하나를 부른다.

    ⛔ 2차 수리는 이것을 `build_envelope` **안쪽에만** 뒀다. 그래서 사냥꾼 3차가
    `Envelope(...)` 직접 생성 · `dataclasses.replace` · `counts` dict 변조 ·
    `object.__setattr__` · 상속 **다섯 경로**로 전부 비켜 갔다.
    검증을 생성 함수에 두면 그 함수를 안 쓰면 그만이다 — **타입이 스스로 지켜야 한다.**
    """
    for k in LINEAGE:
        v = counts.get(k)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            raise ProvenanceError(f"counts.{k}: 유한한 수가 아니다 ({v!r})")
        if v < 0:
            raise ProvenanceError(f"counts.{k}: 음수다 ({v!r})")
    if sum(counts[k] for k in LINEAGE) <= 0:
        raise ProvenanceError("계보 개수가 전부 0 — 무엇을 셌는지 알 수 없다")
    for k in RESIDUAL_KINDS:
        v = resid.get(k)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            raise ProvenanceError(f"residual.{k}: 유한한 수가 아니다 ({v!r})")
    if not math.isfinite(raw):
        raise ProvenanceError("raw_total: 유한한 수가 아니다")
    if rec is not None and not math.isfinite(rec):
        raise ProvenanceError("reconciled_total: 유한한 수가 아니다")
    #: ⛔ **잔차 크기는 정합 여부와 무관하게 본다**(2026-09-04). 예전엔 이 검사가
    #  `rec is None: return` **아래**에 있어서, 정합 안 된 봉투는 `quality=1e17` 을
    #  총계 12,345 옆에 적어도 그대로 통과했다 — 그런데 be-3d 집계는
    #  **전부 미정합**(reconciled_total=None)이라 생산 경로 전체가 이 검사 밖에
    #  있었다. 항등식은 rec 없이 못 재지만 **크기는 raw 만으로 재다.**
    scale = max(abs(raw), abs(rec) if rec is not None else 0.0, 1.0)
    for k in RESIDUAL_KINDS:
        if abs(resid[k]) > _RESIDUAL_MAX_RATIO * scale:
            raise ProvenanceError(
                f"residual.{k}={resid[k]!r} 가 총계({scale!r})의 "
                f"{_RESIDUAL_MAX_RATIO}배를 넘는다 — 장부가 값을 설명하지 못한다")
    if rec is None:
        return
    diff = rec - raw
    #: ⛔ **덧셈 순서에 의존하지 않는다**(사냥꾼 3차 H-5). 고정 순서 `+` 는
    #  {1.0, 1e17, -1e17} 을 어느 칸에 넣느냐로 판정이 갈렸다 — 같은 수인데.
    movable = math.fsum((resid["coverage"], resid["quality"], resid["unallocated"]))
    #: ⚠ **배분 가능 잔차**로 본다 — `scope` 는 건물 밖 몫이라 화해의 증거가 아니다.
    #  (미러를 고치다 정본에 같은 구멍이 있는 걸 찾았다: `residual={"scope":600}` 만
    #   적어 두면 raw 복사가 "화해했다" 로 통과했다. 2026-09-03)
    _movable_abs = math.fsum(abs(resid[k]) for k in ("coverage", "quality", "unallocated"))
    if _close(diff, 0.0) and _close(_movable_abs, 0.0):
        raise ProvenanceError(
            "reconciled_total 이 raw 와 같고 잔차도 비었다 — 화해한 게 아니라 "
            "복사다. 정합이 안 됐으면 reconciled_total=None 으로 둔다")
    if not _close(movable, diff):
        raise ProvenanceError(
            f"잔차가 차이를 설명하지 못한다: reconciled−raw={diff!r} 인데 "
            f"배분 가능 잔차(coverage+quality+unallocated)={movable!r}. "
            "scope 는 건물 밖 몫이라 합계를 움직일 수 없다")


@dataclass(frozen=True)
class Envelope:
    """계보 봉투. **인스턴스 자체가 생성 경로의 증거**다.

    ⚠ 맨 dict 를 받지 않는 이유: 첫 판은 `contract` 문자열만 봐서
    `{"contract": "...v1", "total": 604e9}` 가 인용 가능 판정을 받았다(팀B H-2).
    """

    unit: str
    raw_total: float
    reconciled_total: float | None
    #: ⛔ **읽기 전용 매핑**이다(사냥꾼 3차 C-1 A3). `frozen=True` 는 속성 재대입만
    #  막고 dict 내용 변조는 못 막는다 — `env.counts["missing"]=0` 한 줄로 결손
    #  게이트가 사라졌다. 원장은 봉투의 근거이므로 바꿀 수 없어야 한다.
    counts: Mapping[str, float]
    residual: Mapping[str, float]
    uncertainty: Mapping[str, float] | None
    source_vintage: str | None
    contract: str = "airo/provenance-envelope/v1"
    _pct: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """⛔ **어떤 경로로 만들어져도** 불변식을 통과해야 한다.

        직접 생성 · `dataclasses.replace` · `object.__setattr__` · 상속 전부
        이 자리를 지난다. (사냥꾼 3차 C-1 의 다섯 우회로가 여기서 닫힌다.)
        """
        c = {k: float(self.counts.get(k, 0)) for k in LINEAGE}             if not isinstance(self.counts, MappingProxyType) else dict(self.counts)
        r = {k: float(self.residual.get(k, 0)) for k in RESIDUAL_KINDS}             if not isinstance(self.residual, MappingProxyType) else dict(self.residual)
        _check_invariants(raw=self.raw_total, rec=self.reconciled_total,
                          counts=c, resid=r)
        object.__setattr__(self, "counts", MappingProxyType(c))
        object.__setattr__(self, "residual", MappingProxyType(r))
        if self.uncertainty is not None:
            object.__setattr__(self, "uncertainty",
                               MappingProxyType(dict(self.uncertainty)))

    # ── 원장에서 직접 계산한다(반올림된 요약을 다시 읽지 않는다) ──────────────
    @property
    def n_all(self) -> float:
        """전체 개수 — **비중(pct)의 분모**다. 모든 칸이 든다."""
        return sum(self.counts.values())

    @property
    def n_denominator(self) -> float:
        """⛔ **커버리지의 분모** = covered + missing. `not_applicable` 은 **빠진다**.

        전역 룰 「"없음" 은 한 가지가 아니다」의 핵심이다. 실측 사고: 대상이 아닌 셀을
        분모에 넣어 커버리지를 **30%** 로 보고했는데 실제 대상 기준은 **97%** 였고,
        그 숫자로 3,600 시뮬(≈2.3일)을 권고할 뻔했다.

        ⚠ 이 봉투도 **같은 실수를 하고 있었다**(gpt.txt 2026-09-03 지적):
        `coverage_pct` 가 `n_all` 로 나눠 `not_applicable` 900 이 섞이면
        30% 가 **3%** 로 보였다 — 10배. 정본(`ABSENCE_IN_DENOMINATOR`)이
        무엇이 분모에 드는지 이미 말하고 있었는데 코드가 안 읽었다.
        """
        return self.n_contributing + sum(
            self.counts[k] for k in ABSENCE_IN_DENOMINATOR)

    @property
    def n_contributing(self) -> float:
        return sum(self.counts[k] for k in CONTRIBUTING)

    @property
    def reconciled(self) -> bool:
        return self.reconciled_total is not None

    def pct(self, kind: str) -> float:
        """계보 비중 — **원장에서 매번 계산**한다(팀B M-8: 반올림으로 결손이 사라졌다)."""
        if kind not in LINEAGE:
            raise ProvenanceError(f"모르는 계보: {kind}")
        return 100.0 * self.counts[kind] / self.n_all if self.n_all else 0.0

    @property
    def coverage_pct(self) -> float | None:
        """대상 기준 커버리지. **분모가 0 이면 `None`** — 정의되지 않는다.

        ⛔ 0.0 을 내면 "못 잼" 이 "0%" 로 보여 대시보드에 **거짓 빨강**이 뜬다
        (사냥꾼 3차 H-7). 이 저장소가 세 번 밟은 *"못 잰 것을 실패로 세지 마라"* 와
        정면 충돌이다. 분모 = covered + missing + unknown 이 전부 0 인 경우다.
        """
        d = self.n_denominator
        return 100.0 * self.n_contributing / d if d else None

    def to_dict(self) -> dict:
        """전송용 표현. ⚠ 이 dict 는 **인용 자격의 증거가 아니다** — 검증은 인스턴스로."""
        d = {
            "contract": self.contract, "unit": self.unit,
            "raw_total": self.raw_total,
            "reconciled_total": self.reconciled_total,
            "reconciled": self.reconciled,
            "coverage_pct": (round(self.coverage_pct, 3)
                             if self.coverage_pct is not None else None),
            #: ⚠ 분모를 **함께 낸다** — 이 값 없이 커버리지만 보면 어떤 모집단인지
            #  알 수 없고, 그게 30%↔97% 사고의 형태였다.
            "coverage_denominator": self.n_denominator,
            "n_all": self.n_all,
            "counts": dict(self.counts),
            "residual": dict(self.residual),
            "uncertainty": dict(self.uncertainty) if self.uncertainty else None,
            "source_vintage": self.source_vintage,
        }
        d.update({f"{k}_pct": round(self.pct(k), 3) for k in LINEAGE})
        return d


def build_envelope(*, raw_total: float, lineage_counts: dict[str, float],
                   reconciled_total: float | None = None,
                   residual: dict[str, float] | None = None,
                   uncertainty: dict[str, float] | None = None,
                   source_vintage: str | None = None,
                   unit: str = "kWh") -> Envelope:
    """계보 봉투를 만든다. 계약 위반이면 **예외를 던진다**(빈 값을 만들지 않는다)."""
    raw = _num(raw_total, "raw_total")

    unknown = [k for k in lineage_counts if k not in LINEAGE]
    if unknown:
        raise ProvenanceError(f"모르는 계보: {unknown} (허용: {list(LINEAGE)})")
    counts = {k: _num(lineage_counts.get(k, 0), f"counts.{k}") for k in LINEAGE}
    if any(v < 0 for v in counts.values()):
        raise ProvenanceError("계보 개수가 음수다")
    n_all = sum(counts.values())
    if n_all <= 0:
        raise ProvenanceError("계보 개수가 전부 0 — 무엇을 셌는지 알 수 없다")

    resid = {k: 0.0 for k in RESIDUAL_KINDS}
    if residual:
        bad = [k for k in residual if k not in RESIDUAL_KINDS]
        if bad:
            raise ProvenanceError(f"모르는 잔차 갈래: {bad} (허용: {list(RESIDUAL_KINDS)})")
        for k, v in residual.items():
            resid[k] = _num(v, f"residual.{k}")

    if reconciled_total is not None:
        rec = _num(reconciled_total, "reconciled_total")
        diff = rec - raw
        #: ⛔ **raw 복사는 화해가 아니다**(팀B H-4). 첫 판은 `diff == 0` 이면 검사
        #  전체를 건너뛰어, 그냥 베껴 넣은 값이 `reconciled=True` 로 기록됐다.
        #  화해했다면 **무엇을 화해했는지**(잔차)가 있어야 한다.
        if _close(diff, 0.0) and _close(sum(abs(v) for v in resid.values()), 0.0):
            raise ProvenanceError(
                "reconciled_total 이 raw 와 같고 잔차도 비었다 — 화해한 게 아니라 "
                "복사다. 정합이 안 됐으면 reconciled_total=None 으로 둔다")
        #: ⛔ **항등식**: 잔차가 차이를 설명해야 한다. 첫 판은 "잔차 칸에 뭐라도
        #  적었나" 만 봐서 1e-5 로 1e7 배 스케일이 통과했다(팀B H-3).
        #  ⚠ `scope` 는 **건물 밖 몫이라 우리 합계를 움직이지 않는다** → 항등식에서 뺀다.
        #  그래서 허위 coverage 로 scope 이동을 가리는 우회(팀B H-5)도 함께 막힌다.
        movable = resid["coverage"] + resid["quality"] + resid["unallocated"]
        if not _close(movable, diff):
            raise ProvenanceError(
                f"잔차가 차이를 설명하지 못한다: reconciled−raw={diff!r} 인데 "
                f"배분 가능 잔차(coverage+quality+unallocated)={movable!r}. "
                "scope 는 건물 밖 몫이라 합계를 움직일 수 없다")
    else:
        rec = None

    if uncertainty is not None:
        if not isinstance(uncertainty, dict) or not uncertainty:
            raise ProvenanceError("uncertainty 는 비지 않은 dict 여야 한다")
        u = {k: _num(v, f"uncertainty.{k}") for k, v in uncertainty.items()}
        #: ⛔ **폭 0 구간은 불확실도가 아니다**(팀B H-7) — 점추정을 구간으로 위장한다.
        if {"p05", "p95"} <= set(u):
            if u["p95"] < u["p05"]:
                raise ProvenanceError("uncertainty: p95 < p05 — 구간이 뒤집혔다")
            if _close(u["p95"], u["p05"]):
                raise ProvenanceError(
                    "uncertainty: 폭 0 구간은 점추정이다 — 구간으로 위장하지 마라")
        else:
            raise ProvenanceError(
                f"uncertainty 는 p05·p95 를 반드시 포함한다 (받은 키: {sorted(u)})")
        uncertainty = u

    return Envelope(unit=unit, raw_total=raw, reconciled_total=rec, counts=counts,
                    residual=resid, uncertainty=uncertainty,
                    source_vintage=source_vintage)


def assert_quotable(env: Envelope, *, require_reconciled: bool = False) -> None:
    """이 봉투를 **인용해도 되는가**. 안 되면 예외로 막는다.

    ⚠ 이 저장소의 규율: *"수치엔 측정 조건을 붙여라"*, *"못 잰 것을 통과로 세지 마라"*.
    ⛔ **맨 dict 는 받지 않는다** — 문자열 하나로 인용 자격을 얻던 구멍(팀B H-2).
    """
    if not isinstance(env, Envelope):
        raise ProvenanceError(
            "계보 봉투가 아니다 — build_envelope 로 만든 값만 인용할 수 있다 "
            "(dict 는 전송용이지 자격 증명이 아니다)")
    #: 사후 변조 방지 — 원장으로 다시 센다. 파생 필드를 덮어써도 소용없다.
    if env.n_all <= 0:
        raise ProvenanceError("원장이 비었다")
    if require_reconciled and not env.reconciled:
        raise ProvenanceError(
            "정합되지 않은 값이다(reconciled_total=None) — 상위 통계와 비교해 인용 금지")
    #: ⛔ **불변식을 여기서 다시 센다**(사냥꾼 3차 C-1). 예전엔 `build_envelope`
    #  안에만 있어 타입만 갖추면 무엇이든 인용 가능했다.
    _check_invariants(raw=env.raw_total, rec=env.reconciled_total,
                      counts=env.counts, resid=env.residual)
    #: ⛔ **부재는 `missing` 뿐이 아니다**(사냥꾼 3차 C-2). 예전엔 `missing` 만 봐서
    #  이름을 `unknown` 으로 바꾸기만 하면 커버리지는 똑같은데 게이트만 사라졌다.
    #  `not_applicable` 로 바꾸면 커버리지가 96.9% → 100% 로 **오르기까지** 했다.
    _absent = {k: env.counts[k] for k in ABSENCE_KINDS if env.counts[k] > 0}
    if _absent and env.uncertainty is None:
        raise ProvenanceError(
            f"부재가 있는데 불확실도가 없다 {sorted(_absent)} — "
            "점추정 하나로 부재를 덮지 마라")
    #: ⛔ **커버리지가 정의되지 않으면 인용할 수 없다**(H-7).
    if env.coverage_pct is None:
        raise ProvenanceError(
            "커버리지 분모가 0 이다(대상이 하나도 없다) — 못 잼이지 0% 가 아니다")
    #: ⛔ **불확실도가 부재를 실제로 덮는지 본다**(사냥꾼 3차 A2). `dataclasses.replace`
    #  로 원장만 갈아끼우면 불변식은 통과하고 물려받은 `uncertainty` 가 게이트를
    #  비켜 간다. 구간이 값을 감싸지 않으면 그 불확실도는 이 봉투의 것이 아니다.
    if env.uncertainty is not None:
        u = env.uncertainty
        lo, hi = u.get("p05"), u.get("p95")
        base = env.reconciled_total if env.reconciled else env.raw_total
        if lo is not None and hi is not None and not (lo <= base <= hi):
            raise ProvenanceError(
                f"불확실도 구간 [{lo}, {hi}] 이 값 {base} 를 감싸지 않는다 — "
                "다른 봉투의 구간을 물려받았을 수 있다")
    #: ⛔ `not_applicable` 은 **근거를 함께 적는다**(정본 스키마가 요구한다).
    if env.counts["not_applicable"] > 0 and not env.source_vintage:
        raise ProvenanceError(
            "not_applicable 이 있는데 근거(source_vintage)가 없다 — "
            "근거 없는 '해당 없음' 은 숨기는 것과 구별되지 않는다")


def is_measured(env: Envelope) -> bool:
    """**전부 실측인가.** `calibrated` 도 실측이 아니다 — 실측에 맞춰 보정한 값이다."""
    if not isinstance(env, Envelope):
        raise ProvenanceError("계보 봉투가 아니다")
    #: ⛔ **부재도 본다**(사냥꾼 3차 M-9). 예전엔 출처축만 봐서
    #  `measured=1, unknown=999999` 인 봉투가 "전부 실측" 판정을 받았다.
    if any(env.counts[k] > 0 for k in ABSENCE_KINDS):
        return False
    return all(env.counts[k] == 0 for k in NOT_MEASURED) and env.counts["measured"] > 0
