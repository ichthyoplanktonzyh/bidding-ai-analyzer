"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks, results, export

app = FastAPI(
    title="Bidding AI Analyzer",
    description="高校AI招投标文件自动化采集与AI分析系统",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "bidding-ai-analyzer"}
