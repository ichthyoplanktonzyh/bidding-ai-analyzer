"""Export API routes."""

import json
import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import pandas as pd

from ...task_manager import task_manager

router = APIRouter()


@router.get("/{task_id}/excel")
def export_excel(task_id: str):
    """Export task analysis results as Excel file."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.analyzer_output:
        raise HTTPException(status_code=404, detail="No analysis results available")

    results = []
    try:
        with open(task.analyzer_output, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    results.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")

    # Flatten results for Excel
    rows = []
    for r in results:
        original = r.get("original", {})
        analysis = r.get("analysis", {})
        data = analysis.get("data", {})
        row = {
            "标题": original.get("标题", ""),
            "采购人": original.get("采购人", ""),
            "发布日期": original.get("发布日期", ""),
            "URL": original.get("URL", ""),
            "项目状态": data.get("project_status", ""),
            "项目名称": data.get("project_name", ""),
            "采购方": data.get("purchasing_entity", ""),
            "产品/服务详情": data.get("product_type", ""),
            "预算金额": data.get("budget_amount", ""),
            "中标金额": data.get("winning_bid_amount", ""),
            "供应商": data.get("supplier_name", ""),
            "采购类型": data.get("procurement_type", ""),
            "招标日期": data.get("tender_release_date", ""),
            "中标日期": data.get("bid_award_date", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='分析结果')
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}_results.xlsx"}
    )


@router.get("/{task_id}/csv")
def export_csv(task_id: str):
    """Export task analysis results as CSV file."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.analyzer_output:
        raise HTTPException(status_code=404, detail="No analysis results available")

    results = []
    try:
        with open(task.analyzer_output, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    results.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results file not found")

    rows = []
    for r in results:
        original = r.get("original", {})
        analysis = r.get("analysis", {})
        data = analysis.get("data", {})
        row = {
            "标题": original.get("标题", ""),
            "采购人": original.get("采购人", ""),
            "发布日期": original.get("发布日期", ""),
            "URL": original.get("URL", ""),
            "项目状态": data.get("project_status", ""),
            "项目名称": data.get("project_name", ""),
            "采购方": data.get("purchasing_entity", ""),
            "产品/服务详情": data.get("product_type", ""),
            "预算金额": data.get("budget_amount", ""),
            "中标金额": data.get("winning_bid_amount", ""),
            "供应商": data.get("supplier_name", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}_results.csv"}
    )
