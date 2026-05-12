"""FastAPI application entry point."""

import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks, results, export, keywords

app = FastAPI(
    title="Bidding AI Analyzer",
    description="高校AI招投标文件自动化采集与AI分析系统",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "bidding-ai-analyzer"}


# === WebSocket: Real-time task status push ===

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task status updates."""
    await websocket.accept()

    from ..task_manager import task_manager

    try:
        while True:
            task = task_manager.get_task(task_id)
            if not task:
                await websocket.send_json({"type": "error", "message": "Task not found"})
                await asyncio.sleep(2)
                continue

            payload = {
                "type": "status_update",
                "task_id": task_id,
                "status": task.status.value,
                "progress": task.progress,
                "total_items": task.total_items,
                "analyzed_items": task.analyzed_items,
                "spider_item_count": len(task.spider_results),
                "error": task.error,
                "timestamp": time.time(),
            }
            await websocket.send_json(payload)

            if task.status.value in ("completed", "failed"):
                await websocket.send_json({"type": "pipeline_complete", "status": task.status.value})
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
