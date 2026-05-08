"""Tests for analyzer module."""

import json
import pytest
from bidding_ai_analyzer.analyzer.engine import TenderAnalyzer


class TestTenderAnalyzer:
    """Tests for TenderAnalyzer JSON parsing logic."""

    def test_fetch_failure_handling(self):
        """Test that invalid URLs return error string."""
        analyzer = TenderAnalyzer()
        content = analyzer.fetch_url_content("http://invalid-url-that-does-not-exist.test/")
        assert "[Fetch failed]" in content

    def test_analyze_with_no_api_key(self):
        """Test that missing API key is handled gracefully."""
        analyzer = TenderAnalyzer()
        result = analyzer._analyze_via_deepseek("http://example.com", "test content")
        assert result["success"] is False
