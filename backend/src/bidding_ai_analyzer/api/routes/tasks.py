"""Task management API routes."""

from fastapi import APIRouter, HTTPException

from ..models import TaskCreateRequest, TaskResponse, TaskListResponse, StartAnalysisRequest
from ...task_manager import task_manager, run_task_background

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(req: TaskCreateRequest):
    """Create a new pipeline task and start Stage 1 (spider) in background."""
    task = task_manager.create_task(
        keyword=req.keyword,
        start_time=req.start_time,
        end_time=req.end_time,
        filter_keywords=req.filter_keywords,
    )
    run_task_background(task.id)
    return TaskResponse(**task.to_dict())


@router.get("/", response_model=TaskListResponse)
def list_tasks():
    """List all tasks."""
    tasks = task_manager.list_tasks()
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Get a single task by ID."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.to_dict())


@router.get("/{task_id}/spider-results")
def get_spider_results(task_id: str):
    """Get Stage 1 spider results for display and user selection."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task_id,
        "results": task.spider_results,
        "total": len(task.spider_results),
    }


@router.post("/{task_id}/start-analysis")
def start_analysis(task_id: str, req: StartAnalysisRequest):
    """Manually trigger Stage 2 (AI analysis) with optional item selection."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    from ...task_manager import run_task_background as run_bg

    def _run_analysis():
        task_manager.start_analysis(task_id, req.selected_indices)

    import threading
    thread = threading.Thread(target=_run_analysis, daemon=True)
    thread.start()

    return {"status": "accepted", "task_id": task_id}
