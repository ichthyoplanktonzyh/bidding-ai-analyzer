"""
Background task orchestration — manages the full pipeline:
Stage 1 (spider data collection) -> Stage 2 (AI analysis).
"""

import json
import os
import threading
import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .spider.base import SpiderConfig, TenderSpider
from .strategies.ccgp import CCGPSearchStrategy
from .analyzer.engine import AnalyzerRunner


class TaskStatus(str, Enum):
    PENDING = "pending"
    SPIDERING = "spidering"          # Stage 1 in progress
    AWAITING_DECISION = "awaiting_decision"  # Stage 1 complete, waiting for user
    ANALYZING = "analyzing"          # Stage 2 in progress
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a single pipeline task."""
    id: str
    keyword: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    filter_keywords: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0              # 0-100
    total_items: int = 0
    analyzed_items: int = 0
    spider_output: str = ""
    spider_results: List[Dict] = field(default_factory=list)
    analyzer_output: str = ""
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "keyword": self.keyword,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "filter_keywords": self.filter_keywords,
            "status": self.status.value,
            "progress": self.progress,
            "total_items": self.total_items,
            "analyzed_items": self.analyzed_items,
            "spider_item_count": len(self.spider_results),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class TaskManager:
    """Manages task lifecycle and pipeline execution."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def create_task(self, keyword: str, start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    filter_keywords: Optional[List[str]] = None) -> Task:
        """Create a new pipeline task."""
        task = Task(
            id=str(uuid.uuid4())[:8],
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            filter_keywords=filter_keywords or [],
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict]:
        """List all tasks."""
        return [t.to_dict() for t in self._tasks.values()]

    def run_pipeline(self, task_id: str):
        """Execute Stage 1 (spider) only. Stage 2 requires user trigger."""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            # === Stage 1: Spider ===
            task.status = TaskStatus.SPIDERING
            task.progress = 5

            filter_kw = task.filter_keywords if task.filter_keywords else ['大学', '学院']

            config = SpiderConfig(
                keyword=task.keyword,
                start_time=task.start_time,
                end_time=task.end_time,
                filter_keywords=filter_kw,
                max_pages=100,
                cache_file=f"data/cache_{task.id}.jsonl",
            )
            strategy = CCGPSearchStrategy(config)
            spider = TenderSpider(strategy, config)

            # Progress callback: fires after each page, updates task in real-time
            def on_progress(current_page: int, total_items: int, new_items: int):
                task.total_items = total_items
                # Map page progress into 5-50% range (Stage 1 is half of the pipeline)
                task.progress = min(50, 5 + int((current_page / config.max_pages) * 45))
                # Stream partial results so frontend can show them during crawl
                if new_items > 0:
                    # Append newly crawled items to spider_results
                    new_results = spider.results[-new_items:]
                    task.spider_results.extend([r.to_dict() for r in new_results])

            results = spider.run(progress_callback=on_progress)

            task.total_items = len(results)
            task.progress = 50
            task.spider_output = f"data/spider_{task.id}.jsonl"
            task.spider_results = [r.to_dict() for r in results]
            spider.save_to_jsonl(task.spider_output)

            if not results:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = datetime.now().isoformat()
                return

            # Pause here — wait for user to trigger Stage 2
            task.status = TaskStatus.AWAITING_DECISION
            task.progress = 50

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

    def start_analysis(self, task_id: str, selected_indices: Optional[List[int]] = None):
        """Execute Stage 2 (AI analysis) on user-selected items."""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            task.status = TaskStatus.ANALYZING
            task.progress = 60

            task.analyzer_output = f"data/analyzed_{task.id}.jsonl"
            runner = AnalyzerRunner(max_workers=10, request_delay=1.5)

            if selected_indices:
                # Filter spider results to only selected indices, save temp file
                temp_input = f"data/selected_{task.id}.jsonl"
                selected = [task.spider_results[i] for i in selected_indices if i < len(task.spider_results)]
                os.makedirs("data", exist_ok=True)
                with open(temp_input, 'w', encoding='utf-8') as f:
                    for item in selected:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                analysis_results = runner.run(temp_input, task.analyzer_output)
            else:
                analysis_results = runner.run(task.spider_output, task.analyzer_output)

            task.analyzed_items = sum(1 for r in analysis_results if r.get("analysis", {}).get("success"))
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now().isoformat()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

    def get_spider_results(self, task_id: str) -> List[Dict]:
        """Get Stage 1 spider results for display."""
        task = self.get_task(task_id)
        if not task:
            return []
        return task.spider_results


# Global singleton
task_manager = TaskManager()


def run_task_background(task_id: str):
    """Entry point for running pipeline in a background thread."""
    thread = threading.Thread(target=task_manager.run_pipeline, args=(task_id,), daemon=True)
    thread.start()
