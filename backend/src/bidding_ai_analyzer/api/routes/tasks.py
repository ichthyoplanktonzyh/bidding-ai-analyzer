"""Task management API routes."""

from fastapi import APIRouter, HTTPException

from ..models import TaskCreateRequest, TaskResponse, TaskListResponse
from ...task_manager import task_manager, run_task_background

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(req: TaskCreateRequest):
    """Create a new pipeline task and start it in the background."""
    task = task_manager.create_task(
        keyword=req.keyword,
        start_time=req.start_time,
        end_time=req.end_time,
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
