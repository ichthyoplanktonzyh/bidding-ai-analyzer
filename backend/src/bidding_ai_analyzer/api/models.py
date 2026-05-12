"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    keyword: str = Field(..., description="Search keyword, e.g. AI, 人工智能")
    start_time: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_time: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    filter_keywords: list[str] = Field(
        default_factory=list,
        description="Secondary filter keywords for university matching",
    )


class TaskResponse(BaseModel):
    """Response model for task information."""
    id: str
    keyword: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    filter_keywords: list[str] = []
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


class StartAnalysisRequest(BaseModel):
    """Request model for starting Stage 2 analysis."""
    selected_indices: Optional[list[int]] = Field(
        None, description="Indices of items to analyze; null/empty = analyze all"
    )


class FilterKeywordsRequest(BaseModel):
    """Request model for updating filter keywords preset."""
    name: str = Field(..., description="Preset name")
    keywords: list[str] = Field(..., description="Filter keywords list")


class FilterKeywordsResponse(BaseModel):
    """Response model for filter keywords preset."""
    id: str
    name: str
    keywords: list[str]
    created_at: str
