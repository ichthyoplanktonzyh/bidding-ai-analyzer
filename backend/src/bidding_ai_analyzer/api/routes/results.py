"""Analysis results API routes."""

import json
from fastapi import APIRouter, HTTPException, Query

from ...task_manager import task_manager

router = APIRouter()


@router.get("/{task_id}")
def get_task_results(
    task_id: str,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=500, description="Results per page"),
):
    """Get analysis results for a task with pagination."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.analyzer_output:
        return {"task_id": task_id, "results": [], "total": 0, "success_count": 0}

    results = []
    try:
        with open(task.analyzer_output, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    results.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return {"task_id": task_id, "results": [], "total": 0, "success_count": 0}

    total = len(results)
    success_count = sum(1 for r in results if r.get("analysis", {}).get("success"))
    paged = results[offset:offset + limit]

    return {
        "task_id": task_id,
        "results": paged,
        "total": total,
        "success_count": success_count,
        "offset": offset,
        "limit": limit,
    }
