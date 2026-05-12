"""Filter keywords presets CRUD API."""

import uuid
from fastapi import APIRouter, HTTPException

from ..models import FilterKeywordsRequest, FilterKeywordsResponse
from ...config import DEFAULT_FILTER_KEYWORDS

router = APIRouter()

# In-memory presets store (migrate to DB in v2.0)
_presets: dict[str, dict] = {}

# Seed default preset
_default_id = "default"
_presets[_default_id] = {
    "id": _default_id,
    "name": "默认推荐词库",
    "keywords": list(DEFAULT_FILTER_KEYWORDS),
    "created_at": "2026-05-08T00:00:00",
}


@router.get("/defaults")
def get_default_keywords():
    """Get system default recommended filter keywords."""
    return {"keywords": DEFAULT_FILTER_KEYWORDS}


@router.get("/presets", response_model=list[FilterKeywordsResponse])
def list_presets():
    """List all saved filter keyword presets."""
    return [FilterKeywordsResponse(**p) for p in _presets.values()]


@router.post("/presets", response_model=FilterKeywordsResponse, status_code=201)
def create_preset(req: FilterKeywordsRequest):
    """Create a new filter keyword preset."""
    preset_id = str(uuid.uuid4())[:8]
    from datetime import datetime
    preset = {
        "id": preset_id,
        "name": req.name,
        "keywords": req.keywords,
        "created_at": datetime.now().isoformat(),
    }
    _presets[preset_id] = preset
    return FilterKeywordsResponse(**preset)


@router.put("/presets/{preset_id}", response_model=FilterKeywordsResponse)
def update_preset(preset_id: str, req: FilterKeywordsRequest):
    """Update an existing filter keyword preset."""
    if preset_id not in _presets:
        raise HTTPException(status_code=404, detail="Preset not found")
    _presets[preset_id]["name"] = req.name
    _presets[preset_id]["keywords"] = req.keywords
    return FilterKeywordsResponse(**_presets[preset_id])


@router.delete("/presets/{preset_id}")
def delete_preset(preset_id: str):
    """Delete a filter keyword preset."""
    if preset_id == _default_id:
        raise HTTPException(status_code=400, detail="Cannot delete default preset")
    if preset_id not in _presets:
        raise HTTPException(status_code=404, detail="Preset not found")
    del _presets[preset_id]
    return {"status": "deleted"}
