"""
China Government Procurement Network (CCGP) search strategy.
"""
import re
from typing import List, Dict
from bs4 import BeautifulSoup

from ..spider.base import BaseSearchStrategy, SpiderConfig, TenderItem


class CCGPSearchStrategy(BaseSearchStrategy):
    """Search strategy for http://search.ccgp.gov.cn"""

    def __init__(self, config: SpiderConfig):
        super().__init__(config)
        self.base_url = "http://search.ccgp.gov.cn/bxsearch"
        self.source_name = "中国政府采购网"

    def _get_headers(self) -> Dict:
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'http://search.ccgp.gov.cn/bxsearch',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

    def build_search_url(self, page: int) -> str:
        return self.base_url

    def build_search_params(self, page: int) -> Dict:
        start_time = self.config.start_time.replace('-', ':') if self.config.start_time else ''
        end_time = self.config.end_time.replace('-', ':') if self.config.end_time else ''

        return {
            'searchtype': '1',
            'page_index': str(page),
            'bidSort': '0',
            'buyerName': '',
            'projectId': '',
            'pinMu': '0',
            'bidType': '0',
            'dbselect': 'bidx',
            'kw': self.config.keyword,
            'start_time': start_time,
            'end_time': end_time,
            'timeType': '6',
            'displayZone': '',
            'zoneId': '',
            'pppStatus': '0',
            'agentName': ''
        }

    def pre_request(self, page: int):
        if page == 1:
            try:
                self.session.get("http://www.ccgp.gov.cn/", headers=self.headers, timeout=10)
            except Exception:
                pass

    def parse_results(self, html: str) -> List[TenderItem]:
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('ul.vT-srch-result-list-bid li')

        results = []
        for li in items:
            try:
                a_tag = li.find('a')
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                url = a_tag.get('href', '')

                span_tag = li.find('span')
                if not span_tag:
                    continue

                meta_text = span_tag.get_text(strip=True)
                parts = [p.strip() for p in meta_text.split('|')]

                publish_date = parts[0].split(' ')[0] if parts else ""
                purchaser = ""
                agency = ""
                area = ""

                for p in parts:
                    if '采购人' in p:
                        purchaser = p.replace('采购人：', '').strip()
                    elif '代理机构' in p:
                        agency = p.replace('代理机构：', '').strip()

                if len(parts) >= 4:
                    area = parts[-2].strip() if parts[-1] == "" else parts[-1].strip()

                item = TenderItem(
                    title=title,
                    url=url,
                    publish_date=publish_date,
                    purchaser=purchaser,
                    agency=agency,
                    area=area,
                    source=self.source_name,
                    raw_data={'title': title, 'url': url, 'meta': meta_text}
                )
                results.append(item)

            except Exception:
                continue

        return results

    def detect_blocked(self, html: str) -> bool:
        return "访问受限" in html or "频繁" in html

    def has_more_pages(self, html: str, current_page: int) -> bool:
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('ul.vT-srch-result-list-bid li')
        if len(items) == 0:
            return False
        # Check pagination: CCGP shows total result count, compute max pages
        total_match = re.search(r'共\s*(\d+)\s*条', html)
        if total_match:
            total_results = int(total_match.group(1))
            # CCGP shows 20 results per page
            max_pages = (total_results + 19) // 20
            return current_page < max_pages
        return True
