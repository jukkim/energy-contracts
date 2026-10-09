# -*- coding: utf-8 -*-
"""일상어 동 어간(region_everyday_stems.json dong_stems) — '가정'(가구·전제)은 지명으로 읽지 않고, 그 동의 시도·시군구가 같은 문장에 있으면 읽는다."""
from energy_contracts import regions as R


def test_everyday_dong_stem_blocked_without_region_context():
    for q in ("가정에서 사용하는 전기와 가스 사용량을 비교해줘", "탄소가격 70,000원/tCO2 가정에서 탄소비용", "작년에 가정에서 전기"):
        assert R.everyday_dong_stem_blocked("가정", q) is True, q


def test_region_context_or_non_listed_stem_is_not_blocked():
    for q in ("인천 가정에서 전력", "서구 가정에서", "유성구 가정에서"):
        assert R.everyday_dong_stem_blocked("가정", q) is False, q
    assert R.everyday_dong_stem_blocked("송도", "송도에서 전기") is False


def test_every_listed_dong_stem_is_a_real_dong_and_has_basis():
    import json
    d = json.loads(R.EVERYDAY_STEMS_PATH.read_text(encoding="utf-8"))["dong_stems"]
    assert d                                                          # 0 건 통과 금지
    for stem, meta in d.items():
        r = R.resolve(stem + "동")
        codes = [r.code] if r.ok and r.code else [c.code for c in (r.candidates or [])]
        assert any(c and len(str(c)) == 10 for c in codes), stem       # 실제 법정동 어간이어야 목록에 있을 이유가 있다
        assert meta.get("meaning") and meta.get("basis"), stem
