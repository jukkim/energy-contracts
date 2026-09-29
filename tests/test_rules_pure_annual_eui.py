"""ec_annual_eui — 연간 EUI 정본 규칙(2026-09-29 M5 결정 B'). be-3d canonical_annual_eui 와 같은 뜻. 반례 양쪽."""
import json
from pathlib import Path

import pytest

from energy_contracts.rules_pure import ec_annual_eui

JT = json.loads((Path(__file__).resolve().parents[1] / "energy_contracts/schemas/judgement_thresholds.json")
                .read_text(encoding="utf-8"))["default"]


def months(y, kwh, n=12, sep="-"):
    return {f"{y}{sep}{m:02d}": kwh for m in range(1, n + 1)}


def test_complete_year_gives_calendar_sum_rounded_per_carrier():
    r = ec_annual_eui({"electricity": months(2025, 1000.0), "gas": months(2025, 250.0)}, 100.0, judgement_thresholds=JT)
    assert r["value_kwh_m2_yr"] == 150.0 and r["basis"] == "calendar_year_12_month_sum" and r["absence_kind"] is None
    assert r["eui_by_carrier"] == {"electricity": 120.0, "gas": 30.0} and r["year"] == 2025


def test_held_carrier_short_of_12_months_gives_no_total_not_electricity_only():
    """막아야 할 것 — 가스 11개월을 버리고 전기만으로 총량(= 가스 0 채움). 울산 중구청 2024 사례."""
    r = ec_annual_eui({"electricity": months(2024, 1000.0), "gas": months(2024, 250.0, 11)}, 100.0, judgement_thresholds=JT)
    assert r["value_kwh_m2_yr"] is None and r["absence_kind"] == "missing" and r["code"] == "EUI_NO_COMPLETE_YEAR"


def test_newest_complete_year_is_chosen_and_blank_months_do_not_count():
    series = {**months(2023, 800.0), **months(2024, 900.0, 11), "2024-12": None}
    r = ec_annual_eui({"electricity": series}, 100.0, judgement_thresholds=JT)
    assert r["year"] == 2023 and r["value_kwh_m2_yr"] == 96.0      # 2024 는 빈 달(None) 때문에 11개월 — 온전하지 않다
    assert ec_annual_eui({"electricity": series}, 100.0, year=2024, judgement_thresholds=JT)["code"] == "EUI_YEAR_INCOMPLETE"


def test_implausible_and_non_positive_are_unknown_not_values():
    cap = float(JT["data_quality"]["eui_plausible_kwh_m2"]["max"])
    big = ec_annual_eui({"electricity": months(2025, (cap + 100) * 100 / 12)}, 100.0, judgement_thresholds=JT)
    assert big["value_kwh_m2_yr"] is None and big["absence_kind"] == "unknown" and big["code"] == "EUI_IMPLAUSIBLE"
    zero = ec_annual_eui({"electricity": months(2025, 0.0)}, 100.0, judgement_thresholds=JT)
    assert zero["value_kwh_m2_yr"] is None and zero["code"] == "EUI_TOTAL_NOT_POSITIVE"


def test_missing_area_or_months_are_named_and_cap_comes_from_ec():
    assert ec_annual_eui({"electricity": months(2025, 1.0)}, None, judgement_thresholds=JT)["code"] == "EUI_AREA_MISSING"
    assert ec_annual_eui({}, 100.0, judgement_thresholds=JT)["code"] == "EUI_NO_MONTHS"
    with pytest.raises(LookupError):
        ec_annual_eui({"electricity": months(2025, 1.0)}, 100.0)                 # 생성본 밖 + 인자 없음 = 이름 있는 실패


def test_compact_month_keys_are_accepted():
    r = ec_annual_eui({"electricity": months(2025, 1000.0, sep="")}, 100.0, judgement_thresholds=JT)
    assert r["value_kwh_m2_yr"] == 120.0
