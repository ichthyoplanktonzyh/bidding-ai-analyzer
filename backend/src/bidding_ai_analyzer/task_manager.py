"""
Background task orchestration — manages the full pipeline:
Stage 1 (spider data collection) -> Stage 2 (AI analysis).
"""

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
    SPIDERING = "spidering"       # Stage 1 in progress
    ANALYZING = "analyzing"       # Stage 2 in progress
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a single pipeline task."""
    id: str
    keyword: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0              # 0-100
    total_items: int = 0
    analyzed_items: int = 0
    spider_output: str = ""
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
            "status": self.status.value,
            "progress": self.progress,
            "total_items": self.total_items,
            "analyzed_items": self.analyzed_items,
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
                    end_time: Optional[str] = None) -> Task:
        """Create a new pipeline task."""
        task = Task(
            id=str(uuid.uuid4())[:8],
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
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
        """Execute full pipeline: Stage 1 (spider) -> Stage 2 (analyze)."""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            # === Stage 1: Spider ===
            task.status = TaskStatus.SPIDERING
            task.progress = 10

            config = SpiderConfig(
                keyword=task.keyword,
                start_time=task.start_time,
                end_time=task.end_time,
                filter_keywords=['大学', '学院', '高职', '职业技术', '职业学院', '师范', '理工', '经贸', '学校'],
                max_pages=100,
                cache_file=f"data/cache_{task.id}.jsonl",
            )
            strategy = CCGPSearchStrategy(config)
            spider = TenderSpider(strategy, config)
            results = spider.run()

            task.total_items = len(results)
            task.progress = 50
            task.spider_output = f"data/spider_{task.id}.jsonl"
            spider.save_to_jsonl(task.spider_output)

            if not results:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = datetime.now().isoformat()
                return

            # === Stage 2: Analyze ===
            task.status = TaskStatus.ANALYZING
            task.progress = 60

            task.analyzer_output = f"data/analyzed_{task.id}.jsonl"
            runner = AnalyzerRunner(max_workers=10, request_delay=1.5)
            analysis_results = runner.run(task.spider_output, task.analyzer_output)

            task.analyzed_items = sum(1 for r in analysis_results if r.get("analysis", {}).get("success"))
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now().isoformat()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)


# Global singleton
task_manager = TaskManager()


def run_task_background(task_id: str):
    """Entry point for running pipeline in a background thread."""
    thread = threading.Thread(target=task_manager.run_pipeline, args=(task_id,), daemon=True)
    thread.start()
