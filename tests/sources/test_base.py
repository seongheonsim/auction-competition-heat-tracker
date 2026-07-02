from auction_tracker.sources.base import FactsAdapter, ViewCountAdapter
from auction_tracker.sources.types import PropertyFacts, SourceName, ViewCountResult


class _FakeFacts:
    source = SourceName.COURTAUCTION

    def fetch_facts(self, *, case_no=None, item_no=None, onbid_no=None):
        return PropertyFacts(source=self.source, appraisal_price=1)


class _FakeViews:
    source = SourceName.GGI

    def fetch_view_count(self, *, case_no, item_no=None):
        return ViewCountResult(source=self.source, view_count=7)


def test_facts_adapter_runtime_checkable():
    assert isinstance(_FakeFacts(), FactsAdapter)
    assert not isinstance(_FakeViews(), FactsAdapter)


def test_view_count_adapter_runtime_checkable():
    assert isinstance(_FakeViews(), ViewCountAdapter)
    assert not isinstance(_FakeFacts(), ViewCountAdapter)
