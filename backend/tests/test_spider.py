"""Tests for spider module."""

import pytest
from bidding_ai_analyzer.spider.base import SpiderConfig, TenderItem, TenderSpider


class TestTenderItem:
    """Tests for TenderItem data class."""

    def test_to_dict(self):
        item = TenderItem(
            title="Test Project",
            url="http://example.com/test",
            publish_date="2025-01-01",
            purchaser="Test University",
            source="Test Source",
        )
        d = item.to_dict()
        assert d['标题'] == "Test Project"
        assert d['URL'] == "http://example.com/test"
        assert d['发布日期'] == "2025-01-01"
        assert d['采购人'] == "Test University"
        assert d['来源'] == "Test Source"

    def test_to_dict_defaults(self):
        item = TenderItem(title="Test", url="http://example.com")
        d = item.to_dict()
        assert d['代理机构'] == ""
        assert d['所在区域'] == ""


class TestSpiderConfig:
    """Tests for SpiderConfig."""

    def test_default_values(self):
        config = SpiderConfig(keyword="AI")
        assert config.keyword == "AI"
        assert config.max_pages == 100
        assert config.delay_range == (3, 8)


class TestTenderSpider:
    """Tests for TenderSpider dedup logic."""

    def test_url_dedup(self):
        config = SpiderConfig(keyword="AI", use_cache=False)
        # We test filtering logic via _filter_item directly
        from bidding_ai_analyzer.spider.base import BaseSearchStrategy

        class MockStrategy(BaseSearchStrategy):
            def _get_headers(self):
                return {}

            def build_search_url(self, page):
                return ""

            def build_search_params(self, page):
                return {}

            def parse_results(self, html):
                return []

            def detect_blocked(self, html):
                return False

            def has_more_pages(self, html, page):
                return False

        strategy = MockStrategy(config)
        spider = TenderSpider(strategy, config)

        # Test filter logic
        item1 = TenderItem(title="XX大学AI平台采购", url="http://a.com/1", purchaser="北京大学")
        item2 = TenderItem(title="XX公司IT设备采购", url="http://a.com/2", purchaser="某公司")

        config.filter_keywords = ['大学']
        assert spider._filter_item(item1) is True
        assert spider._filter_item(item2) is False
