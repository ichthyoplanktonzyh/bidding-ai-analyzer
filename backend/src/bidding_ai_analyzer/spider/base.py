"""
Generic tender information spider framework.
Supports multiple data sources via strategy pattern.
Each website's query logic, parsing, and filtering are configurable.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class SpiderConfig:
    """Spider configuration."""
    keyword: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    filter_keywords: List[str] = field(default_factory=list)
    max_pages: int = 100
    delay_range: tuple = (3, 8)
    timeout: int = 20
    use_cache: bool = True
    cache_file: str = "data/raw_data_cache.jsonl"


@dataclass
class TenderItem:
    """Standardized tender data structure."""
    title: str
    url: str
    publish_date: str = ""
    purchaser: str = ""
    agency: str = ""
    area: str = ""
    source: str = ""
    raw_data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            '标题': self.title,
            'URL': self.url,
            '发布日期': self.publish_date,
            '采购人': self.purchaser,
            '代理机构': self.agency,
            '所在区域': self.area,
            '来源': self.source,
            '原始数据': self.raw_data
        }


class BaseSearchStrategy(ABC):
    """Abstract base class for search strategies."""

    def __init__(self, config: SpiderConfig):
        self.config = config
        self.session = requests.Session()
        self.headers = self._get_headers()

    @abstractmethod
    def _get_headers(self) -> Dict:
        """Return HTTP headers for requests."""
        pass

    @abstractmethod
    def build_search_url(self, page: int) -> str:
        """Build search URL for given page."""
        pass

    @abstractmethod
    def build_search_params(self, page: int) -> Dict:
        """Build query parameters for given page."""
        pass

    @abstractmethod
    def parse_results(self, html: str) -> List[TenderItem]:
        """Parse search result HTML into TenderItem list."""
        pass

    @abstractmethod
    def detect_blocked(self, html: str) -> bool:
        """Detect if the request was blocked by anti-scraping measures."""
        pass

    @abstractmethod
    def has_more_pages(self, html: str, current_page: int) -> bool:
        """Determine if more result pages exist."""
        pass

    def pre_request(self, page: int):
        """Hook executed before each page request."""
        pass

    def post_request(self, page: int, response: requests.Response):
        """Hook executed after each page request."""
        pass


class TenderSpider:
    """Generic spider engine."""

    def __init__(self, strategy: BaseSearchStrategy, config: SpiderConfig):
        self.strategy = strategy
        self.config = config
        self.results: List[TenderItem] = []
        self._load_cache()

    def _load_cache(self):
        """Load previously crawled data from cache file."""
        if not self.config.use_cache:
            return

        cache_path = self.config.cache_file
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item_data = json.loads(line)
                        if not any(r.url == item_data.get('URL', '') for r in self.results):
                            self.results.append(TenderItem(
                                title=item_data.get('标题', ''),
                                url=item_data.get('URL', ''),
                                publish_date=item_data.get('发布日期', ''),
                                purchaser=item_data.get('采购人', ''),
                                agency=item_data.get('代理机构', ''),
                                area=item_data.get('所在区域', ''),
                                source=item_data.get('来源', '')
                            ))
                    except Exception:
                        continue
            print(f"Loaded {len(self.results)} items from cache")

    def _save_to_cache(self, item: TenderItem):
        """Append a single item to the cache file."""
        if not self.config.use_cache:
            return

        os.makedirs(os.path.dirname(self.config.cache_file) or '.', exist_ok=True)
        with open(self.config.cache_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + '\n')

    def fetch_page(self, page: int) -> Optional[str]:
        """Fetch HTML content for a given page."""
        self.strategy.pre_request(page)

        params = self.strategy.build_search_params(page)
        url = self.strategy.build_search_url(page)

        for retry in range(3):
            try:
                response = self.strategy.session.get(
                    url,
                    params=params,
                    headers=self.strategy.headers,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                self.strategy.post_request(page, response)
                return response.text
            except Exception as e:
                print(f"Page {page} request failed (attempt {retry + 1}/3): {e}")
                time.sleep(10)

        return None

    def parse_and_filter(self, html: str, page: int) -> int:
        """Parse page and apply keyword filters."""
        items = self.strategy.parse_results(html)
        new_count = 0

        for item in items:
            if self._filter_item(item):
                if not any(r.url == item.url for r in self.results):
                    self.results.append(item)
                    self._save_to_cache(item)
                    new_count += 1

        return new_count

    def _filter_item(self, item: TenderItem) -> bool:
        """Apply keyword filter to a tender item."""
        if not self.config.filter_keywords:
            return True

        text_to_check = (item.title + item.purchaser).lower()
        return any(kw.lower() in text_to_check for kw in self.config.filter_keywords)

    def run(self, start_page: int = 1, progress_callback=None) -> List[TenderItem]:
        """Run the spider, collecting results from all pages.

        Args:
            start_page: Page to start crawling from.
            progress_callback: Optional callable(current_page, total_items, new_items).
        """
        print(f"Starting spider: keyword='{self.config.keyword}'")
        print(f"Filter keywords: {self.config.filter_keywords}")
        print(f"Page range: {start_page} - {self.config.max_pages}")
        print("-" * 50)

        consecutive_empty = 0  # Track pages with 0 new items

        for page in range(start_page, self.config.max_pages + 1):
            print(f"[{time.strftime('%H:%M:%S')}] Requesting page {page}...", end=' ')

            html = self.fetch_page(page)
            if not html:
                print("Request failed, stopping")
                break

            if self.strategy.detect_blocked(html):
                print("\nBlocked detected, stopping")
                break

            new_count = self.parse_and_filter(html, page)

            # Report progress after each page
            if progress_callback:
                progress_callback(page, len(self.results), new_count)

            # Stop if strategy says no more pages
            if not self.strategy.has_more_pages(html, page):
                print("\nLast page reached (strategy)")
                break

            # Auto-stop: 2 consecutive pages with 0 new items = no more data
            if new_count == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    print(f"\nNo new results for {consecutive_empty} pages, stopping early at page {page}")
                    break
            else:
                consecutive_empty = 0

            print(f"Got {new_count} new items, total {len(self.results)}")

            delay = random.uniform(*self.config.delay_range)
            time.sleep(delay)

        print("-" * 50)
        print(f"Crawl complete: {len(self.results)} items total")
        return self.results

    def save_to_jsonl(self, filename: str):
        """Save results to JSONL file."""
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            for item in self.results:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + '\n')
        print(f"Saved to: {filename}")

    def save_to_excel(self, filename: str):
        """Save results to Excel file."""
        if not self.results:
            print("No data to save")
            return

        data = [item.to_dict() for item in self.results]
        df = pd.DataFrame(data)
        cols = ['标题', '采购人', '代理机构', '所在区域', '发布日期', 'URL', '来源']
        df = df[[c for c in cols if c in df.columns]]
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        df.to_excel(filename, index=False)
        print(f"Saved to: {filename}")

    def get_unique_urls(self) -> List[str]:
        """Get deduplicated URL list."""
        return [item.url for item in self.results]
