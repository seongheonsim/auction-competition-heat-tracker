import datetime as dt

from auction_tracker.sources.types import (
    PropertyFacts,
    SourceError,
    SourceName,
    ViewCountResult,
)


def test_source_name_values():
    assert SourceName.GGI.value == "ggi"
    assert SourceName("courtauction") is SourceName.COURTAUCTION


def test_property_facts_defaults():
    f = PropertyFacts(source=SourceName.COURTAUCTION)
    assert f.appraisal_price is None
    assert f.raw == {}
    f2 = PropertyFacts(source=SourceName.COURTAUCTION, sale_price=100, result_type="매각")
    assert f2.sale_price == 100 and f2.result_type == "매각"


def test_view_count_result_defaults():
    v = ViewCountResult(source=SourceName.GGI, view_count=42)
    assert v.view_count == 42
    assert v.sale_ratio is None
    assert v.raw == {}


def test_source_error_carries_source():
    err = SourceError(SourceName.TANK, "parse failed")
    assert err.source is SourceName.TANK
    assert "tank" in str(err)
    assert err.message == "parse failed"
