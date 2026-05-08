"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    keyword: str = Field(..., description="Search keyword, e.g. AI, 人工智能")
    start_time: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_time: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class TaskResponse(BaseModel):
    """Response model for task information."""
    id: str
    keyword: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: str
    progress: int
    total_items: int
    analyzed_items: int
    created_at: str
    completed_at: Optional[str] = None
    error: str = ""


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: list[TaskResponse]
    total: int


class AnalysisResultItem(BaseModel):
    """A single analyzed result."""
    index: int
    original: dict
    analysis: dict


class AnalysisResultResponse(BaseModel):
    """Response model for analysis results."""
    task_id: str
    results: list[AnalysisResultItem]
    total: int
    success_count: int
