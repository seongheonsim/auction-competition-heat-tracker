from pathlib import Path

from auction_tracker.sources.adapters.onbid import OnbidAdapter
from auction_tracker.sources.adapters.tank import TankAdapter
from auction_tracker.sources.base import FactsAdapter, ViewCountAdapter
from auction_tracker.sources.types import PropertyFacts, SourceName, ViewCountResult

FIX = Path(__file__).parent.parent / "fixtures"


def test_onbid_adapter_returns_facts():
    content = (FIX / "onbid" / "item.json").read_text(encoding="utf-8")
    adapter = OnbidAdapter(fetcher=lambda key: content)
    facts = adapter.fetch_facts(onbid_no="2026-0600-033681")
    assert isinstance(facts, PropertyFacts)
    assert facts.source is SourceName.ONBID
    assert facts.appraisal_price == 644000000
    assert facts.min_price == 381000000
    assert facts.fail_count == 5


def test_onbid_adapter_none_without_onbid_no():
    adapter = OnbidAdapter(fetcher=lambda key: "{}")
    assert adapter.fetch_facts(case_no="2024타경1") is None


def test_tank_adapter_returns_view_count():
    content = (FIX / "tank" / "list.json").read_text(encoding="utf-8")
    adapter = TankAdapter(fetcher=lambda key: content)
    res = adapter.fetch_view_count(case_no="2020타경16401")
    assert isinstance(res, ViewCountResult)
    assert res.source is SourceName.TANK
    assert res.view_count == 147


def test_tank_adapter_none_for_unknown_case():
    content = (FIX / "tank" / "list.json").read_text(encoding="utf-8")
    adapter = TankAdapter(fetcher=lambda key: content)
    assert adapter.fetch_view_count(case_no="1999타경1") is None


def test_adapters_satisfy_protocols():
    assert isinstance(OnbidAdapter(fetcher=lambda k: "{}"), FactsAdapter)
    assert isinstance(TankAdapter(fetcher=lambda k: "[]"), ViewCountAdapter)
