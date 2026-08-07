"""소비단이 요청한 **계약 축**이 서 있는가 (MGCC EC 선행 5건, 2026-08-07).

MGCC 가 "이건 계약이 먼저 서야 우리가 못 닫는다" 며 5건을 올려 보냈다:
어휘 정합(연료·열에 계수를 못 붙인다) · APE 상태가 계약 밖 · 요금의 지역/시간대 축
부재 · `_consumers` 누락 · `fleet/heartbeat` 가 경로로만 식별.

값을 넣는 것으로 끝내면 **다음에 값이 늘 때 같은 자리가 다시 갈라진다** — 두 축이
서로를 대조하게 만든다.
"""
from energy_contracts import load_schema


def _s(name):
    return load_schema(name)


# ── 두 축이 서로를 가리키는가 (MGCC EC 선행 5건, 2026-08-07) ──────────────────
#
# 소비단(MGCC)이 "계약이 먼저 서야 못 닫는다" 며 5건을 올려 보냈다. 값을 넣는 것으로
# 끝내면 **다음에 값이 늘 때 같은 자리가 다시 갈라진다** — 두 축이 서로를 대조하게
# 만든다.

def test_emission_factor_keys_are_energy_carriers():
    """배출계수 키는 **`EnergyCarrier` 의 부분집합**이어야 한다.

    예전엔 계수 키(electricity/gas/district_heat)와 `EnergySource`
    (electricity/fuel/heat/renewable)의 **교집합이 전기 하나**였다 — 연료·열을
    보고하는 건물의 CO₂ 는 원리적으로 계산 불가였고, 소비단은 이름만 남겼다.
    """
    carriers = set(_s("telemetry")["$defs"]["EnergyCarrier"]["enum"])
    factors = _s("emission_factors")["default"]["co2_kgco2eq_per_kwh"]
    for region, keys in factors.items():
        unknown = sorted(set(keys) - carriers)
        assert not unknown, (
            f"{region} 배출계수에 운반체 어휘 밖 키: {unknown} — "
            "소비단이 그 키를 어디에도 붙일 수 없다")


def test_energy_source_and_carrier_stay_separate_axes():
    """카테고리와 운반체를 **한 축으로 합치지 않는다**.

    `fuel` 이 도시가스인지 등유인지 기계적으로 정할 수 없다 — 합치면 소비단이
    추측 매핑을 하게 되고, 그 추측이 배출량으로 나간다.
    """
    t = _s("telemetry")
    source = set(t["$defs"]["EnergySource"]["enum"])
    carrier = set(t["$defs"]["EnergyCarrier"]["enum"])
    assert "fuel" in source and "fuel" not in carrier
    assert "gas" in carrier and "gas" not in source
    assert "electricity" in source & carrier, "전기는 두 축에서 같은 뜻이다"


def test_ape_state_is_declared_where_the_screen_reads_it():
    """MGCC 상시 운영 평면이 **계약 밖 필드**에 얹혀 있지 않다.

    엣지가 이름을 바꾸면 전 멤버가 `unknown` 이 되는데, 그건 규율상 정당한 표시라
    **통신 장애와 배선 파손이 화면에서 구분되지 않는다**.
    """
    t = _s("telemetry")
    assert "ape" in t["properties"]
    ape = t["$defs"]["ApeState"]["properties"]
    assert set(ape) >= {"persona", "strategy"}
    assert ape["persona"]["$ref"].endswith("ObjectiveType"), (
        "페르소나 값집합이 운영 목적 축과 다른 곳을 가리킨다")
    # 하위호환 — 기존 필드를 빼지 않았다.
    assert "active_strategy" in t["properties"]


#: 지금 **페이로드 계약도 사유도 없는** 채널. 각 채널의 소유 repo 가 채워야 한다 —
#: 내가 남의 채널에 "왜 없는지" 를 지어 적을 수는 없다(그게 더 나쁘다).
#: ⚠ 이 목록은 **줄기만 해야** 한다. 새 채널이 여기 들어오려 하면 게이트가 막는다.
_UNDOCUMENTED_TOPICS = frozenset({
    "gridbridge/schedule/{ven_id}",
    "gridbridge/ack/{ven_id}",
    "gridbridge/alert/{ven_id}",
    "vworld/telemetry/{ven_id}",
    "vworld/alert/{ven_id}",
    "agentleague/challenge/{challenge_id}/result",
    "agentleague/control/{ven_id}",
    "eduarena/match/{match_id}/event",
    "eduarena/judge/{match_id}",
})


def test_no_new_topic_is_identified_by_path_alone():
    """토픽이 **경로로만** 식별되면 EC 가 이름을 바꿀 때 소비단이 못 따라간다.

    소비단은 경로 꼬리로 찾아가는 우회를 이미 갖고 있지만(MGCC `topics.py`),
    그건 계약이 아니라 추측이다 — 네임스페이스가 바뀌면 조용히 fallback 으로
    떨어지고 화면엔 아무 표시도 없다.

    기존 공백은 소유 repo 가 채우기 전까지 이름으로 남긴다. 이 게이트가 막는 것은
    **새로 생기는 침묵**이다.
    """
    rows = _s("mqtt_topics")["default"]["topics"]
    silent = {r["pattern"] for r in rows
              if not r.get("payload_schema") and not r.get("$comment")}
    new = sorted(silent - _UNDOCUMENTED_TOPICS)
    assert not new, (
        "payload_schema 도 사유도 없는 **새** 채널 — 이름이 바뀌면 조용히 끊긴다: "
        + ", ".join(new))
    healed = sorted(_UNDOCUMENTED_TOPICS - silent)
    assert not healed, (
        "이 채널들은 이제 계약을 갖췄다 — 목록에서 지울 것(목록은 줄기만 한다): "
        + ", ".join(healed))


def test_heartbeat_is_no_longer_path_identified():
    """MGCC 가 올린 5건 중 하나 — 하트비트가 자기 페이로드 계약을 갖는다."""
    rows = _s("mqtt_topics")["default"]["topics"]
    hb = [r for r in rows if r["pattern"] == "fleet/heartbeat/{ven_id}"][0]
    assert hb["payload_schema"].endswith("edge_status.json")


def test_tariff_can_carry_its_region_and_timezone():
    """요금 계약이 **어느 지역·시간대**인지 실을 수 있다.

    `additionalProperties: false` 라 자리가 없으면 소비단이 실어 보낼 방법이 없고,
    그 결과 비-KR 그룹도 한국 요금표·KST 로 계산된다.
    """
    props = _s("tariff_contract")["properties"]
    assert "region_code" in props and "timezone" in props
    assert _s("tariff_contract")["additionalProperties"] is False, (
        "자리를 만들었다고 문을 열어 두면 오타가 조용히 통과한다")


def test_consumers_list_matches_who_actually_subscribes():
    """구독하는 repo 는 `_consumers` 에 있어야 한다 — 계약이 그 사실을 알아야 갱신이 간다."""
    assert "mgcc" in _s("telemetry")["_consumers"]
    assert "mgcc" in _s("edge_status")["_consumers"]


def test_fuel_carriers_have_a_price_axis():
    """연료·열에도 **요금을 실을 자리**가 있다 (MGCC C1 월 청구 대조, 2026-08-07).

    전에는 `tou_energy_krw_per_kwh`(전기 전용)뿐이라, 가스 사용량이 도착해도
    금액을 낼 방법이 없었다 — MGCC 는 "EC 에 가스 요금 축이 없다" 는 사유로
    **거절**하고 있었다(지어내지 않은 건 옳지만, 계약이 막고 있던 것이다).

    ⚠ 운반체 키는 **`EnergyCarrier` 에서 파생**한다. 손으로 적으면 EC 가 운반체를
    늘릴 때 이 축만 뒤처진다(값이 아니라 **출처**가 갈라지는 결함).
    """
    t = _s("tariff_contract")
    carriers = [c for c in _s("telemetry")["$defs"]["EnergyCarrier"]["enum"]
                if c != "electricity"]
    for field in ("fuel_energy_krw_per_kwh", "fuel_base_charge_krw_per_month"):
        assert field in t["properties"], f"{field} 자리가 없다"
        keys = set(t["properties"][field]["properties"])
        assert keys == set(carriers), (
            f"{field} 의 운반체가 EnergyCarrier 와 갈라졌다: "
            f"없음={set(carriers) - keys} 남음={keys - set(carriers)}")
        assert t["properties"][field]["additionalProperties"] is False


def test_electricity_is_not_in_the_fuel_axis():
    """전기는 **TOU 축**에 있다 — 두 자리에 두면 어느 쪽이 참인지 모른다."""
    t = _s("tariff_contract")["properties"]
    assert "electricity" not in t["fuel_energy_krw_per_kwh"]["properties"]
    assert "off_peak" in t["tou_energy_krw_per_kwh"]["properties"]


def test_mgcc_is_listed_as_a_tariff_consumer():
    """MGCC 가 요금 계약을 가장 많이 쓰는데 `_consumers` 에 없었다.

    계약이 소비자를 모르면 스키마가 바뀔 때 갱신이 그 repo 로 가지 않는다.
    """
    assert "mgcc" in _s("tariff_contract")["_consumers"]
