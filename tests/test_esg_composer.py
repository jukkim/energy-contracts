"""esg composer SSOT 단위 테스트.

순수 함수 compose_scope + embodied_key + 9 sub-bucket parity + overrides 화이트리스트.
"""

from __future__ import annotations

import pytest

from energy_contracts.esg import (
    EMBODIED_AMORTIZATION_YEARS,
    OVERRIDE_ALLOWED,
    ScopeBreakdown,
    ScopeFactors,
    ScopeInputs,
    compose_scope,
    embodied_key,
)


# ── 공통 factor fixture ─────────────────────────────────────────────


def _fxs(
    gas: float = 0.2036,        # CO2_FACTOR_GAS
    elec: float = 0.4173,       # CO2_FACTOR_ELECTRICITY
    heat: float = 0.1260,       # CO2_FACTOR_DISTRICT_HEAT
    refrig: float = 0.5,        # 냉매 (업무시설 가정)
    embodied: float = 800.0,    # RC_2010_2017 ~800 kgCO2/m²
    td_loss: float = 0.04,      # 4% 송배전 손실
    occ: float = 0.05,          # 0.05 person/m² (업무시설)
    commute: float = 100.0,     # 100 kgCO2/person·yr
    waste: float = 2.0,         # 2 kgCO2/m²·yr
    water: float = 1.5,         # 1.5 kgCO2/m²·yr
) -> ScopeFactors:
    return ScopeFactors(
        gas_kg_per_kwh=gas,
        electricity_kg_per_kwh=elec,
        heat_kg_per_kwh=heat,
        refrigerant_kg_per_m2=refrig,
        embodied_kg_per_m2=embodied,
        td_loss_rate=td_loss,
        occupancy_density=occ,
        commute_kg_per_person=commute,
        waste_kg_per_m2=waste,
        water_kg_per_m2=water,
    )


# ── ScopeBreakdown properties ──────────────────────────────────────


class TestScopeBreakdownProperties:
    def test_scope_1_total_is_sum(self):
        b = ScopeBreakdown(100.0, 50.0, 0, 0, 0, 0, 0, 0, 0)
        assert b.scope_1_total == 150.0

    def test_scope_2_total_is_sum(self):
        b = ScopeBreakdown(0, 0, 200.0, 75.0, 0, 0, 0, 0, 0)
        assert b.scope_2_total == 275.0

    def test_scope_3_total_is_sum(self):
        b = ScopeBreakdown(0, 0, 0, 0, 10, 20, 30, 40, 50)
        assert b.scope_3_total == 150.0

    def test_total_co2_kg(self):
        b = ScopeBreakdown(100, 50, 200, 75, 10, 20, 30, 40, 50)
        # s1=150, s2=275, s3=150 → 575
        assert b.total_co2_kg == 575.0

    def test_to_dict_keys(self):
        b = ScopeBreakdown(100, 50, 200, 75, 10, 20, 30, 40, 50)
        d = b.to_dict()
        for key in (
            "scope_1_gas_co2_kg", "scope_1_refrigerant_co2_kg", "scope_1_total_co2_kg",
            "scope_2_electricity_co2_kg", "scope_2_heat_co2_kg", "scope_2_total_co2_kg",
            "scope_3_embodied_co2_kg", "scope_3_td_loss_co2_kg",
            "scope_3_commute_co2_kg", "scope_3_waste_co2_kg", "scope_3_water_co2_kg",
            "scope_3_total_co2_kg", "total_co2_kg",
        ):
            assert key in d


# ── Composer math ──────────────────────────────────────────────────


class TestComposeScope:
    def test_zero_area_returns_all_zero(self):
        b = compose_scope(ScopeInputs(area_m2=0.0), _fxs())
        assert b.total_co2_kg == 0.0

    def test_negative_area_returns_all_zero(self):
        b = compose_scope(ScopeInputs(area_m2=-100.0), _fxs())
        assert b.total_co2_kg == 0.0

    def test_scope_1_gas_formula(self):
        # 100 kWh/m² × 1000 m² × 0.2036 = 20360
        b = compose_scope(
            ScopeInputs(area_m2=1000.0, gas_kwh_m2=100.0),
            _fxs(refrig=0.0),  # refrig 제거하여 단독 검증
        )
        assert b.scope_1_gas == pytest.approx(20360.0)
        assert b.scope_1_refrigerant == 0.0

    def test_scope_1_refrigerant_formula(self):
        # 0.5 × 1000 = 500
        b = compose_scope(
            ScopeInputs(area_m2=1000.0),  # no gas
            _fxs(refrig=0.5),
        )
        assert b.scope_1_refrigerant == 500.0

    def test_scope_2_electricity_formula(self):
        # 200 × 1000 × 0.4173 = 83460
        b = compose_scope(
            ScopeInputs(area_m2=1000.0, electricity_kwh_m2=200.0),
            _fxs(),
        )
        assert b.scope_2_electricity == pytest.approx(83460.0)

    def test_scope_2_heat_formula(self):
        # 50 × 1000 × 0.1260 = 6300
        b = compose_scope(
            ScopeInputs(area_m2=1000.0, heat_kwh_m2=50.0),
            _fxs(),
        )
        assert b.scope_2_heat == pytest.approx(6300.0)

    def test_scope_3_embodied_amortized_50yr(self):
        # embodied 800 / 50 × 1000 = 16000
        b = compose_scope(
            ScopeInputs(area_m2=1000.0),
            _fxs(embodied=800.0),
        )
        assert b.scope_3_embodied == pytest.approx(16000.0)

    def test_scope_3_td_loss_formula(self):
        # 200 × 1000 × 0.04 × 0.4173 = 3338.4
        b = compose_scope(
            ScopeInputs(area_m2=1000.0, electricity_kwh_m2=200.0),
            _fxs(),
        )
        assert b.scope_3_td_loss == pytest.approx(3338.4)

    def test_scope_3_commute_formula(self):
        # 0.05 × 1000 × 100 = 5000
        b = compose_scope(
            ScopeInputs(area_m2=1000.0),
            _fxs(),
        )
        assert b.scope_3_commute == pytest.approx(5000.0)

    def test_scope_3_waste_formula(self):
        # 2.0 × 1000 = 2000
        b = compose_scope(ScopeInputs(area_m2=1000.0), _fxs())
        assert b.scope_3_waste == 2000.0

    def test_scope_3_water_formula(self):
        # 1.5 × 1000 = 1500
        b = compose_scope(ScopeInputs(area_m2=1000.0), _fxs())
        assert b.scope_3_water == 1500.0

    def test_amortization_constant(self):
        # SSOT 상수 노출 확인
        assert EMBODIED_AMORTIZATION_YEARS == 50


# ── Manual overrides 화이트리스트 ────────────────────────────────


class TestManualOverrides:
    def test_override_allowed_replaces_computed(self):
        b = compose_scope(
            ScopeInputs(
                area_m2=1000.0,
                gas_kwh_m2=100.0,
                manual_overrides={"scope_1_gas_co2_kg": 99999.0},
            ),
            _fxs(refrig=0.0),
        )
        assert b.scope_1_gas == 99999.0  # computed 20360 무시

    def test_override_unknown_key_ignored(self):
        # 화이트리스트 외 키 — 무시
        b = compose_scope(
            ScopeInputs(
                area_m2=1000.0,
                gas_kwh_m2=100.0,
                manual_overrides={"scope_1_total_co2_kg": 0.0, "evil_field": 1e9},
            ),
            _fxs(refrig=0.0),
        )
        # scope_1_total 은 computed 값 유지
        assert b.scope_1_gas == pytest.approx(20360.0)

    def test_override_non_float_ignored(self):
        # 변환 실패 → computed 그대로
        b = compose_scope(
            ScopeInputs(
                area_m2=1000.0,
                gas_kwh_m2=100.0,
                manual_overrides={"scope_1_gas_co2_kg": "not a number"},
            ),
            _fxs(refrig=0.0),
        )
        assert b.scope_1_gas == pytest.approx(20360.0)

    def test_override_zero_allowed(self):
        # 의도적 0 (실측 없음) → 0 적용
        b = compose_scope(
            ScopeInputs(
                area_m2=1000.0,
                gas_kwh_m2=100.0,
                manual_overrides={"scope_1_gas_co2_kg": 0.0},
            ),
            _fxs(refrig=0.0),
        )
        assert b.scope_1_gas == 0.0

    def test_override_whitelist_is_9_buckets(self):
        assert len(OVERRIDE_ALLOWED) == 9


# ── embodied_key normalization ─────────────────────────────────────


class TestEmbodiedKey:
    def test_canonical_rc_2010(self):
        assert embodied_key("RC", "2010_2017") == "RC_2010_2017"

    def test_canonical_s(self):
        assert embodied_key("S", "pre1980") == "S_pre1980"

    def test_canonical_w_any_vintage(self):
        # 목조 — 연대 무관
        assert embodied_key("W", "2010_2017") == "W_any"
        assert embodied_key("W", "pre1980") == "W_any"

    def test_korean_structure_keywords(self):
        assert embodied_key("철골", "2010_2017") == "S_2010_2017"
        assert embodied_key("조적", "1980_2000") == "M_1980_2000"
        assert embodied_key("벽돌조", "1980_2000") == "M_1980_2000"
        assert embodied_key("목조", "2017") == "W_any"
        assert embodied_key("철근콘크리트", "2010") == "RC_2010_2017"

    def test_english_lowercase(self):
        assert embodied_key("steel", "2010") == "S_2010_2017"
        assert embodied_key("masonry", "1980") == "M_1980_2000"
        assert embodied_key("wood", "2017") == "W_any"

    def test_be3d_legacy_vintage_y2010(self):
        # be-3d 'y2010' → '2010_2017'
        assert embodied_key("RC", "y2010") == "RC_2010_2017"

    def test_be3d_legacy_vintage_pre1980(self):
        assert embodied_key("RC", "pre1980") == "RC_pre1980"

    def test_be3d_legacy_vintage_post2017(self):
        assert embodied_key("RC", "post2017") == "RC_post2017"
        assert embodied_key("RC", "y2017") == "RC_post2017"

    def test_unknown_structure_defaults_to_rc(self):
        # 알 수 없는 구조 → RC
        assert embodied_key("unknown", "2010_2017") == "RC_2010_2017"

    def test_empty_inputs_default(self):
        # None/empty vintage → "_default" (be-3d 원본 동작 보존)
        assert embodied_key(None, None) == "_default"
        assert embodied_key("", "") == "_default"

    def test_none_vintage_with_canonical_structure(self):
        # vintage None → _default (be-3d 호환)
        assert embodied_key("RC", None) == "_default"
        assert embodied_key("S", "") == "_default"


# ── Parity: GB calculator 동작 보존 ───────────────────────────────


class TestParityGB:
    """GB src/scope/calculator.py::calculate_scope 동작 보존 검증.

    동일 입력 + 동일 factor 주입 시 동일 9 sub-bucket 반환.
    """

    def test_gb_full_scenario(self):
        # GB scenario: 업무시설 1000 m², 전력 200/가스 100/난방 0
        b = compose_scope(
            ScopeInputs(
                area_m2=1000.0,
                electricity_kwh_m2=200.0,
                gas_kwh_m2=100.0,
                heat_kwh_m2=0.0,
            ),
            _fxs(),
        )
        # GB 의 raw 계산식과 일치 확인
        assert b.scope_1_gas == pytest.approx(20360.0)
        assert b.scope_1_refrigerant == 500.0
        assert b.scope_2_electricity == pytest.approx(83460.0)
        assert b.scope_2_heat == 0.0
        assert b.scope_3_embodied == pytest.approx(16000.0)
        assert b.scope_3_td_loss == pytest.approx(3338.4)
        assert b.scope_3_commute == 5000.0
        assert b.scope_3_waste == 2000.0
        assert b.scope_3_water == 1500.0


class TestParityBE3D:
    """be-3d src/simulation/scope_emissions.py::calculate_all_scopes 동작 보존."""

    def test_be3d_scenario(self):
        # be-3d 예시 (모듈 docstring): 75 m² 판매시설, 전력 800/가스 50/난방 0
        b = compose_scope(
            ScopeInputs(
                area_m2=75.0,
                electricity_kwh_m2=800.0,
                gas_kwh_m2=50.0,
                heat_kwh_m2=0.0,
            ),
            _fxs(),
        )
        # 단순 산식 검증
        assert b.scope_1_gas == pytest.approx(50 * 75 * 0.2036)
        assert b.scope_2_electricity == pytest.approx(800 * 75 * 0.4173)


class TestOverrideValueGuard:
    """사냥꾼 라운드 M3 (2026-06-08): override 값 검증 — NaN/Inf/음수/bool 차단."""

    def _base(self, overrides):
        return compose_scope(
            ScopeInputs(area_m2=100.0, electricity_kwh_m2=100.0, manual_overrides=overrides),
            _fxs(),
        )

    def test_nan_override_ignored(self):
        b = self._base({"scope_1_gas_co2_kg": float("nan")})
        import math
        assert math.isfinite(b.total_co2_kg), "NaN override 가 total 을 오염시키면 안 됨"

    def test_inf_override_ignored(self):
        b = self._base({"scope_2_electricity_co2_kg": float("inf")})
        import math
        assert math.isfinite(b.total_co2_kg)

    def test_negative_override_ignored(self):
        # 음수 배출량은 물리적으로 무의미 → computed 유지
        computed = self._base({}).scope_1_gas
        b = self._base({"scope_1_gas_co2_kg": -100.0})
        assert b.scope_1_gas == computed

    def test_bool_override_ignored(self):
        computed = self._base({}).scope_3_waste
        b = self._base({"scope_3_waste_co2_kg": True})
        assert b.scope_3_waste == computed

    def test_valid_override_applied(self):
        b = self._base({"scope_1_gas_co2_kg": 42.5})
        assert b.scope_1_gas == 42.5


class TestEmbodiedKeyVintageOrdering:
    """사냥꾼 라운드 LOW (2026-06-08): 범위 라벨은 시작연도 기준 분류."""

    def test_range_label_uses_start_year(self):
        # '2010-2017' 은 post2017 이 아니라 2010_2017 (시작연도 2010)
        assert embodied_key("RC", "2010-2017") == "RC_2010_2017"

    def test_bare_2017_still_post(self):
        assert embodied_key("RC", "y2017") == "RC_post2017"

    def test_post_label_still_post(self):
        assert embodied_key("RC", "post") == "RC_post2017"

    def test_canonical_unchanged(self):
        assert embodied_key("RC", "2010_2017") == "RC_2010_2017"
        assert embodied_key("S", "post2017") == "S_post2017"
