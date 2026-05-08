"""
Additional bidding platform search strategies.
Currently supports CTBPP (China Tendering & Bidding Public Service Platform)
and ChinaBidding.
"""
from typing import List, Dict
from bs4 import BeautifulSoup

from ..spider.base import BaseSearchStrategy, SpiderConfig, TenderItem


class CTBPPSearchStrategy(BaseSearchStrategy):
    """China Tendering & Bidding Public Service Platform strategy."""

    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.base_url = "http://bulletin.cebpubservice.com"
        self.search_path = "/search/s"
        self.source_name = "招标投标公共服务平台"

    def _get_headers(self) -> Dict:
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

    def build_search_url(self, page: int) -> str:
        return self.base_url + self.search_path

    def build_search_params(self, page: int) -> Dict:
        params = {
            'pageIndex': page,
            'pageSize': 20,
            'keyword': self.config.keyword,
        }
        if self.config.start_time:
            params['startTime'] = self.config.start_time
        if self.config.end_time:
            params['endTime'] = self.config.end_time
        return params

    def parse_results(self, html: str) -> List[TenderItem]:
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('.search-result-list li, .result-list li, .list-item')

        results = []
        for li in items:
            try:
                a_tag = li.find('a')
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                url = a_tag.get('href', '')

                date_elem = li.find('span', class_='date') or li.find('.time')
                publish_date = date_elem.get_text(strip=True) if date_elem else ""

                purchaser_elem = li.find('.purchaser') or li.find('.buyer')
                purchaser = purchaser_elem.get_text(strip=True) if purchaser_elem else ""

                agency_elem = li.find('.agency') or li.find('.agent')
                agency = agency_elem.get_text(strip=True) if agency_elem else ""

                item = TenderItem(
                    title=title,
                    url=url,
                    publish_date=publish_date,
                    purchaser=purchaser,
                    agency=agency,
                    source=self.source_name,
                    raw_data={'title': title, 'url': url}
                )
                results.append(item)

            except Exception:
                continue

        return results

    def detect_blocked(self, html: str) -> bool:
        return "访问受限" in html or "频繁" in html or "请验证" in html

    def has_more_pages(self, html: str, current_page: int) -> bool:
        soup = BeautifulSoup(html, 'html.parser')
        next_btn = soup.select('.pagination .next, .page-next')
        return next_btn and 'disabled' not in str(next_btn[0].get('class', []))


class ChinaBiddingSearchStrategy(BaseSearchStrategy):
    """ChinaBidding search strategy."""

    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.base_url = "http://www.chinabidding.cn"
        self.source_name = "中国招标网"

    def _get_headers(self) -> Dict:
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

    def build_search_url(self, page: int) -> str:
        return f"{self.base_url}/search"

    def build_search_params(self, page: int) -> Dict:
        return {
            'keywords': self.config.keyword,
            'page': page,
            'date': self.config.start_time or '',
        }

    def parse_results(self, html: str) -> List[TenderItem]:
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('.tender-list li, .info-list li')

        results = []
        for li in items:
            try:
                a_tag = li.find('a')
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                url = a_tag.get('href', '')

                item = TenderItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    raw_data={'title': title, 'url': url}
                )
                results.append(item)

            except Exception:
                continue

        return results

    def detect_blocked(self, html: str) -> bool:
        return "访问受限" in html or "请输入验证码" in html

    def has_more_pages(self, html: str, current_page: int) -> bool:
        soup = BeautifulSoup(html, 'html.parser')
        pagination = soup.select('.pagination a, .pages a')
        return len(pagination) > 0
