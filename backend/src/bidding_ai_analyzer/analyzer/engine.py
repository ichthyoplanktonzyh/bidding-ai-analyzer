"""
AI-powered tender document analysis engine.
Fetches tender detail pages and extracts structured information via LLM.
"""

import json
import requests
import time
import re
import threading
import os
from typing import Dict, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    MODEL_NAME,
    MAX_CONTENT_LENGTH,
)

PROMPT = """# Role
You are an expert assistant specializing in analyzing university AI-related bidding/tender documents. Your task is to accurately and efficiently extract key structured information from any tender document text I provide.

# Task
Carefully read and understand the provided [Tender Document Text], then extract the relevant information according to the [Output Field Definitions] below, and return the result in strict JSON format.

# Output Field Definitions
Extract information from the text according to the following field descriptions. If a field is not explicitly mentioned in the original text or cannot be found, set its value to `null`.

- `project_status`: Project status (e.g.: 招标中, 已中标, 已废标, 资格预审).
- `tender_release_date`: Tender release date (publication date of the project announcement or tender documents).
- `bid_award_date`: Bid award date (publication date of the winning bid announcement).
- `purchasing_entity`: Purchasing entity (full name of the purchaser/tenderer/procuring unit, usually a university name).
- `project_name`: Project name (official full name of this bidding project).
- `purchaser_info`: Purchaser contact info (contact person, phone number, address, etc.).
- `product_type`: **Product/Service Details (Key field: Please describe in detail the core products, services, or solutions being procured. The goal is to accurately understand the specific content of the project procurement, especially related to AI and university business. Do NOT use generic terms like "Goods", "Services", or "Engineering").**
- `budget_amount`: Budget amount (project budget control amount, including both uppercase and lowercase forms).
- `winning_bid_amount`: Winning bid amount (final transaction amount of the winning supplier).
- `supplier_name`: Supplier name (full name of the winning bidder).
- `procurement_type`: Procurement type (procurement organization form, e.g.: 公开招标, 邀请招标, 竞争性谈判, 单一来源采购).
- `tender_notice_url`: Tender notice URL (link to the original announcement).
- `procurement_documents`: Procurement documents (information related to procurement documents, such as file names, download links, etc.).

# Output Format Requirements
- The output must be a single, complete, and properly formatted JSON object.
- The keys of the JSON object must strictly use the English field names provided in the [Output Field Definitions].
- Do not add any extra explanations, notes, or comments beyond the JSON object.
"""


class TenderAnalyzer:
    """Analyzes individual tender documents using LLM APIs."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        })

    def fetch_url_content(self, url: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
        """Fetch and clean HTML content from a URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            content = response.text

            # Remove scripts and styles
            clean_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            clean_content = re.sub(r'<style[^>]*>.*?</style>', '', clean_content, flags=re.DOTALL | re.IGNORECASE)
            # Remove HTML tags
            clean_content = re.sub(r'<[^>]+>', ' ', clean_content)
            # Collapse whitespace
            clean_content = re.sub(r'\s+', ' ', clean_content)
            clean_content = clean_content.strip()

            if len(clean_content) > max_length:
                clean_content = clean_content[:max_length] + "..."

            return clean_content
        except Exception as e:
            return f"[Fetch failed] {str(e)}"

    def analyze_tender(self, url: str, content: str) -> Dict:
        """Call DeepSeek API to analyze a single tender document."""
        return self._analyze_via_deepseek(url, content)

    def _analyze_via_deepseek(self, url: str, content: str) -> Dict:
        """Analyze via DeepSeek API directly."""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        user_prompt = f"""Please analyze the following tender document content and extract structured information:

[Tender Document Text]:
{content}

[Tender Notice URL]: {url}

Return only the JSON result without any explanation."""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                content_result = result["choices"][0]["message"]["content"]

                json_match = re.search(r'\{[\s\S]*\}', content_result)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return {"success": True, "data": parsed}
                else:
                    return {"success": False, "error": "Cannot parse JSON from response", "raw": content_result}
            else:
                return {"success": False, "error": f"API error: {response.status_code}", "detail": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


class AnalyzerRunner:
    """Manages concurrent batch analysis of tender records."""

    def __init__(self, max_workers: int = 10, request_delay: float = 1.5):
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.output_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        self.processed_count = 0
        self.total_count = 0

    def _process_single_record(self, idx: int, record: Dict, output_file: str) -> Dict:
        """Process a single tender record."""
        url = record.get("URL", "")

        if not url:
            result = {
                "index": idx,
                "original": record,
                "analysis": {"success": False, "error": "No URL"}
            }
            self._save_result(result, output_file)
            return result

        analyzer = TenderAnalyzer()

        with self.progress_lock:
            print(f"[{self.processed_count + 1}/{self.total_count}] Fetching: {url[:50]}...")

        content = analyzer.fetch_url_content(url)

        if "[Fetch failed]" in content:
            result = {
                "index": idx,
                "original": record,
                "analysis": {"success": False, "error": content}
            }
            with self.progress_lock:
                self.processed_count += 1
            self._save_result(result, output_file)
            return result

        with self.progress_lock:
            print(f"[{self.processed_count + 1}/{self.total_count}] Content length: {len(content)}, analyzing...")

        analysis_result = analyzer.analyze_tender(url, content)

        result = {
            "index": idx,
            "original": record,
            "analysis": analysis_result
        }

        with self.progress_lock:
            self.processed_count += 1
            status = "success" if analysis_result.get("success") else "failed"
            print(f"[{self.processed_count}/{self.total_count}] Analysis {status}")

        self._save_result(result, output_file)
        return result

    def _save_result(self, result: Dict, output_file: str):
        """Thread-safe incremental save to output file."""
        with self.output_lock:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

    def run(self, input_file: str, output_file: str, max_records: Optional[int] = None) -> List[Dict]:
        """Run batch analysis on a JSONL input file."""
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        records = []
        for i, line in enumerate(lines):
            try:
                record = json.loads(line.strip())
                records.append((i, record))
            except Exception:
                continue

        if max_records:
            records = records[:max_records]

        self.total_count = len(records)
        self.processed_count = 0

        print(f"\n{'=' * 50}")
        print(f"Multi-threaded analysis mode")
        print(f"Total tasks: {self.total_count}")
        print(f"Concurrent workers: {self.max_workers}")
        print(f"Request delay: {self.request_delay}s")
        print(f"{'=' * 50}\n")

        # Clear output file
        with open(output_file, 'w', encoding='utf-8') as f:
            pass

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for idx, record in records:
                future = executor.submit(self._process_single_record, idx, record, output_file)
                futures.append(future)
                time.sleep(self.request_delay)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Task execution error: {e}")

        results.sort(key=lambda x: x.get("index", 0))

        success_count = sum(1 for r in results if r.get("analysis", {}).get("success"))
        print(f"\n{'=' * 50}")
        print(f"Complete! Processed {len(results)} records, {success_count} successful")
        print(f"Results saved to: {output_file}")
        print(f"{'=' * 50}")
        return results
