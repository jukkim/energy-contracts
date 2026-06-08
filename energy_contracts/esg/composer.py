"""ESG Scope 1/2/3 순수 composer.

수학:
    Scope 1 = gas_kwh_m2 × area × gas_factor
            + refrigerant_factor × area
    Scope 2 = electricity_kwh_m2 × area × elec_factor
            + heat_kwh_m2 × area × heat_factor
    Scope 3 = (embodied_factor / EMBODIED_AMORTIZATION_YEARS) × area
            + electricity_kwh_m2 × area × td_loss_rate × elec_factor
            + occupancy_density × area × commute_factor
            + waste_factor × area
            + water_factor × area

manual_overrides 는 화이트리스트 (OVERRIDE_ALLOWED) 안에서만 적용.

호출자가 모든 factor 를 사전 lookup 후 `ScopeFactors` 로 주입한다 (DB/cache
의존성 격리). 본 composer 는 순수 함수 — 부수효과 없음.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# 내재탄소 상각 기간 (년). GB / be-3d 양쪽 동일 (50yr).
# 변경 시 본 상수만 갱신 → 두 도메인 동시 반영.
EMBODIED_AMORTIZATION_YEARS: int = 50

# manual_overrides 허용 키 — 9 sub-bucket. 외 키는 무시 (보안: 외부 입력 화이트리스트).
OVERRIDE_ALLOWED: frozenset[str] = frozenset({
    "scope_1_gas_co2_kg",
    "scope_1_refrigerant_co2_kg",
    "scope_2_electricity_co2_kg",
    "scope_2_heat_co2_kg",
    "scope_3_embodied_co2_kg",
    "scope_3_td_loss_co2_kg",
    "scope_3_commute_co2_kg",
    "scope_3_waste_co2_kg",
    "scope_3_water_co2_kg",
})


@dataclass(frozen=True)
class ScopeInputs:
    """건물 입력 데이터 — 면적 + 에너지 강도 + 수동 override.

    Attributes:
        area_m2: 연면적 (m²). 0 이하 → 전부 0 반환.
        electricity_kwh_m2: 전력 사용 강도 (kWh/m²·yr)
        gas_kwh_m2: 가스 사용 강도 (kWh/m²·yr)
        heat_kwh_m2: 지역난방 사용 강도 (kWh/m²·yr)
        manual_overrides: 9 sub-bucket 별 외부 입력값 (kgCO2). 화이트리스트 외 키 무시.
    """
    area_m2: float
    electricity_kwh_m2: float = 0.0
    gas_kwh_m2: float = 0.0
    heat_kwh_m2: float = 0.0
    manual_overrides: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeFactors:
    """모든 배출계수 사전 lookup 결과 — composer 가 pure function 동작.

    호출자 책임:
        - DB scope_factors / emission_factors 테이블 조회
        - standard ("kr"/"eu") / year 분기
        - 단위 환산 (kg vs ton, kWh vs MJ)

    Attributes:
        gas_kg_per_kwh: 가스 직접 연소 배출계수 (kgCO2/kWh)
        electricity_kg_per_kwh: 전력 배출계수 (kgCO2/kWh)
        heat_kg_per_kwh: 지역난방 배출계수 (kgCO2/kWh)
        refrigerant_kg_per_m2: 냉매 누출 원단위 (kgCO2/m²·yr, usage_type 의존)
        embodied_kg_per_m2: 내재탄소 raw 원단위 (kgCO2/m², 50년 상각 전 — composer 가 분할)
        td_loss_rate: 송배전 손실률 (0~1, 무차원)
        occupancy_density: 재실밀도 (person/m², usage_type 의존)
        commute_kg_per_person: 통근 배출계수 (kgCO2/person·yr, region 의존)
        waste_kg_per_m2: 폐기물 원단위 (kgCO2/m²·yr, usage_type 의존)
        water_kg_per_m2: 용수 원단위 (kgCO2/m²·yr, usage_type 의존)
    """
    gas_kg_per_kwh: float
    electricity_kg_per_kwh: float
    heat_kg_per_kwh: float
    refrigerant_kg_per_m2: float
    embodied_kg_per_m2: float
    td_loss_rate: float
    occupancy_density: float
    commute_kg_per_person: float
    waste_kg_per_m2: float
    water_kg_per_m2: float


@dataclass(frozen=True)
class ScopeBreakdown:
    """Scope 1/2/3 9 sub-bucket + total. 모든 값 kgCO2.

    합계는 property 로 derive — 9 sub-bucket 만 저장 (override 후 재계산 안 잊음).
    """
    scope_1_gas: float
    scope_1_refrigerant: float
    scope_2_electricity: float
    scope_2_heat: float
    scope_3_embodied: float
    scope_3_td_loss: float
    scope_3_commute: float
    scope_3_waste: float
    scope_3_water: float

    @property
    def scope_1_total(self) -> float:
        return self.scope_1_gas + self.scope_1_refrigerant

    @property
    def scope_2_total(self) -> float:
        return self.scope_2_electricity + self.scope_2_heat

    @property
    def scope_3_total(self) -> float:
        return (
            self.scope_3_embodied
            + self.scope_3_td_loss
            + self.scope_3_commute
            + self.scope_3_waste
            + self.scope_3_water
        )

    @property
    def total_co2_kg(self) -> float:
        return self.scope_1_total + self.scope_2_total + self.scope_3_total

    def to_dict(self, *, decimals: int = 2) -> dict[str, float]:
        """평탄화 dict — DB UPSERT / JSON 응답에 사용.

        키 명명은 GB venue_scope_emissions 테이블 컬럼과 일치 (scope_N_*_co2_kg).
        """
        return {
            "scope_1_gas_co2_kg": round(self.scope_1_gas, decimals),
            "scope_1_refrigerant_co2_kg": round(self.scope_1_refrigerant, decimals),
            "scope_1_total_co2_kg": round(self.scope_1_total, decimals),
            "scope_2_electricity_co2_kg": round(self.scope_2_electricity, decimals),
            "scope_2_heat_co2_kg": round(self.scope_2_heat, decimals),
            "scope_2_total_co2_kg": round(self.scope_2_total, decimals),
            "scope_3_embodied_co2_kg": round(self.scope_3_embodied, decimals),
            "scope_3_td_loss_co2_kg": round(self.scope_3_td_loss, decimals),
            "scope_3_commute_co2_kg": round(self.scope_3_commute, decimals),
            "scope_3_waste_co2_kg": round(self.scope_3_waste, decimals),
            "scope_3_water_co2_kg": round(self.scope_3_water, decimals),
            "scope_3_total_co2_kg": round(self.scope_3_total, decimals),
            "total_co2_kg": round(self.total_co2_kg, decimals),
        }


_ZERO_BREAKDOWN = ScopeBreakdown(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def compose_scope(inputs: ScopeInputs, factors: ScopeFactors) -> ScopeBreakdown:
    """Scope 1/2/3 9 sub-bucket 계산 + manual_overrides 화이트리스트 적용.

    area<=0 일 때 모든 값 0 반환 (호출자가 사전 검증해도 됨).
    """
    area = inputs.area_m2 or 0.0
    if area <= 0:
        return _ZERO_BREAKDOWN

    # ── Scope 1 ──
    gas = inputs.gas_kwh_m2 * area * factors.gas_kg_per_kwh
    refrigerant = factors.refrigerant_kg_per_m2 * area

    # ── Scope 2 ──
    electricity = inputs.electricity_kwh_m2 * area * factors.electricity_kg_per_kwh
    heat = inputs.heat_kwh_m2 * area * factors.heat_kg_per_kwh

    # ── Scope 3 ──
    embodied = (factors.embodied_kg_per_m2 / EMBODIED_AMORTIZATION_YEARS) * area
    td_loss = (
        inputs.electricity_kwh_m2 * area
        * factors.td_loss_rate * factors.electricity_kg_per_kwh
    )
    commute = factors.occupancy_density * area * factors.commute_kg_per_person
    waste = factors.waste_kg_per_m2 * area
    water = factors.water_kg_per_m2 * area

    # ── Manual overrides (whitelist) ──
    overrides = inputs.manual_overrides or {}
    gas = _override(overrides, "scope_1_gas_co2_kg", gas)
    refrigerant = _override(overrides, "scope_1_refrigerant_co2_kg", refrigerant)
    electricity = _override(overrides, "scope_2_electricity_co2_kg", electricity)
    heat = _override(overrides, "scope_2_heat_co2_kg", heat)
    embodied = _override(overrides, "scope_3_embodied_co2_kg", embodied)
    td_loss = _override(overrides, "scope_3_td_loss_co2_kg", td_loss)
    commute = _override(overrides, "scope_3_commute_co2_kg", commute)
    waste = _override(overrides, "scope_3_waste_co2_kg", waste)
    water = _override(overrides, "scope_3_water_co2_kg", water)

    return ScopeBreakdown(
        scope_1_gas=gas,
        scope_1_refrigerant=refrigerant,
        scope_2_electricity=electricity,
        scope_2_heat=heat,
        scope_3_embodied=embodied,
        scope_3_td_loss=td_loss,
        scope_3_commute=commute,
        scope_3_waste=waste,
        scope_3_water=water,
    )


def _override(overrides: dict[str, Any], key: str, computed: float) -> float:
    """화이트리스트 통과 시 override, 아니면 computed 그대로.

    사냥꾼 라운드 M3 (2026-06-08): manual_overrides 는 외부 입력 화이트리스트(보안
    경계)인데 float() 변환 성공만 보고 값을 검증하지 않아 NaN/Inf/음수/bool 이
    그대로 통과 → total_co2_kg 가 NaN 으로 조용히 오염(DB UPSERT/JSON 전파)됐다.
    이제 finite ∧ ≥0 인 실수만 적용하고, 그 외(NaN/Inf/음수/bool/비수치)는 computed 유지.
    """
    if key in OVERRIDE_ALLOWED and key in overrides:
        raw = overrides[key]
        # bool 은 int 하위형 — kgCO2 값으로 의미 없음, 명시 차단.
        if isinstance(raw, bool):
            return computed
        try:
            val = float(raw)
        except (TypeError, ValueError):
            return computed
        if not math.isfinite(val) or val < 0:
            return computed
        return val
    return computed
