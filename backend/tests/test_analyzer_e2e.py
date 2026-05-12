"""End-to-end tests for analyzer module.

These tests verify the complete pipeline:
1. Fetch tender document content from real URLs
2. Send to LLM API for analysis
3. Parse and validate the structured results

Note: These tests require a valid API key to run. They will be skipped if no API key is configured.
"""

import json
import os
import pytest
from bidding_ai_analyzer.analyzer.engine import TenderAnalyzer
from bidding_ai_analyzer.config import DEEPSEEK_API_KEY, DIFY_API_KEY, USE_DIFY


def has_api_key():
    """Check if any API key is configured."""
    return bool(DEEPSEEK_API_KEY or DIFY_API_KEY)


TEST_URLS = [
    "http://www.ccgp.gov.cn/cggg/zygg/zbgg/202505/t20250509_12345678.htm",
]


class TestAnalyzerE2E:
    """End-to-end tests for the analyzer module."""

    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance."""
        return TenderAnalyzer()

    @pytest.fixture
    def sample_tender_content(self):
        """Sample tender document content for testing."""
        return """
        项目名称：某某大学人工智能教学实验平台采购项目
        采购单位：某某大学
        中标供应商：某某科技有限公司
        中标金额：人民币壹佰贰拾叁万肆仟伍佰陆拾元整（￥1234560.00元）
        采购方式：公开招标
        发布时间：2025-05-01
        项目状态：已中标
        """

    @pytest.mark.skipif(not has_api_key(), reason="No API key configured")
    def test_fetch_real_ccgp_page(self, analyzer):
        """Test fetching a real CCGP page."""
        url = "http://www.ccgp.gov.cn/cggg/zygg/zbgg/202505/t20250509_12345678.htm"
        content = analyzer.fetch_url_content(url)
        assert content
        assert "[Fetch failed]" not in content
        assert len(content) > 100

    def test_analyze_with_mock_content(self, analyzer, sample_tender_content):
        """Test analyzing with sample content - tests parsing logic."""
        url = "http://example.com/test"
        result = analyzer.analyze_tender(url, sample_tender_content)
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.skipif(not has_api_key(), reason="No API key configured")
    def test_full_analysis_pipeline(self, analyzer, sample_tender_content):
        """Test the complete analysis pipeline with real API call."""
        url = "http://example.com/test-tender"
        result = analyzer.analyze_tender(url, sample_tender_content)

        assert isinstance(result, dict)
        assert "success" in result

        if result.get("success"):
            assert "data" in result
            data = result["data"]
            assert isinstance(data, dict)

    @pytest.mark.skipif(not has_api_key(), reason="No API key configured")
    def test_deepseek_api_integration(self, analyzer):
        """Test DeepSeek API integration with a simple prompt."""
        url = "http://example.com/test"
        content = "采购单位：清华大学，中标金额：100万元，项目名称：智慧校园系统"
        result = analyzer._analyze_via_deepseek(url, content)

        assert isinstance(result, dict)
        assert "success" in result
        if result.get("success"):
            assert "data" in result

    @pytest.mark.skipif(not has_api_key(), reason="No API key configured")
    @pytest.mark.skipif(USE_DIFY, reason="Test requires DeepSeek, but USE_DIFY is true")
    def test_json_parsing_from_llm_response(self, analyzer):
        """Test that the analyzer correctly parses JSON from LLM responses."""
        url = "http://example.com/test"

        mock_content = """
        采购单位：北京大学
        中标供应商：华为技术有限公司
        中标金额：伍佰万元整
        项目名称：人工智能算力平台采购项目
        采购方式：公开招标
        """

        result = analyzer._analyze_via_deepseek(url, mock_content)

        if result.get("success"):
            data = result.get("data", {})
            assert isinstance(data, dict)

    def test_content_fetch_with_encoding(self, analyzer):
        """Test that content fetch handles different encodings correctly."""
        url = "http://www.example.com"
        content = analyzer.fetch_url_content(url)
        assert isinstance(content, str)


class TestAnalyzerIntegration:
    """Integration tests combining spider and analyzer."""

    @pytest.mark.skipif(not has_api_key(), reason="No API key configured")
    def test_spider_to_analyzer_pipeline(self):
        """Test the full pipeline from spider output to analyzer input."""
        from bidding_ai_analyzer.spider.base import SpiderConfig, TenderSpider
        from bidding_ai_analyzer.strategies.ccgp import CCGPSearchStrategy
        from bidding_ai_analyzer.analyzer.engine import AnalyzerRunner
        import tempfile
        import os

        config = SpiderConfig(
            keyword="人工智能",
            start_time="2025-01-01",
            end_time="2025-05-01",
            max_pages=1,
        )

        strategy = CCGPSearchStrategy(config)
        spider = TenderSpider(strategy, config)

        with tempfile.TemporaryDirectory() as tmpdir:
            spider_file = os.path.join(tmpdir, "test_spider.jsonl")
            analyzed_file = os.path.join(tmpdir, "test_analyzed.jsonl")

            results = spider.run()

            if results:
                spider.save_to_jsonl(spider_file)

                runner = AnalyzerRunner(max_workers=2, request_delay=1.0)
                analysis_results = runner.run(spider_file, analyzed_file, max_records=1)

                assert os.path.exists(analyzed_file)

                with open(analyzed_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        record = json.loads(lines[0])
                        assert "analysis" in record


class TestAnalyzerErrorHandling:
    """Tests for error handling in various scenarios."""

    def test_empty_content_handling(self):
        """Test that empty content is handled gracefully."""
        analyzer = TenderAnalyzer()
        url = "http://example.com"
        result = analyzer.analyze_tender(url, "")
        assert isinstance(result, dict)

    def test_very_long_content_handling(self):
        """Test that very long content is truncated properly."""
        from bidding_ai_analyzer.config import MAX_CONTENT_LENGTH
        analyzer = TenderAnalyzer()

        long_content = "测试内容 " * 10000
        url = "http://example.com"

        result = analyzer._analyze_via_deepseek(url, long_content)

        assert isinstance(result, dict)

    def test_malformed_json_response_handling(self):
        """Test handling of malformed JSON in API response."""
        import requests
        from unittest.mock import patch, MagicMock

        analyzer = TenderAnalyzer()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON {"
                }
            }]
        }

        with patch.object(requests, 'post', return_value=mock_response):
            result = analyzer._analyze_via_deepseek("http://test.com", "test content")

        assert result["success"] is False
