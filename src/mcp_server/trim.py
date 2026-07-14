from typing import Any, Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import os,sys
from src.utils.util_log import log_info, log_error, log_trace, log_warning
from vmodal.models import SearchResponse_frontui, IndexationJobsListResponse


def _text_snippet(raw: Any) -> str:
    if raw is None:
        return ""
    text = str(raw)
    return text[:200]


def trim_search(resp: SearchResponse_frontui, verbose: bool = False) -> Dict[str, Any]:
    source = []
    if hasattr(resp, "data"):
        source = getattr(resp, "data") or []
    if not isinstance(source, list):
        source = []
    limit = int(getattr(resp, "cnt_actual", 0) or len(source))
    if not verbose:
        limit = min(limit, 20)
    rows = []
    for item in source[:limit]:
        if hasattr(item, "model_dump"):
            item = item.model_dump(exclude_none=True)
        if not isinstance(item, dict):
            item = {}
        rows.append(
            {
                "score": item.get("score"),
                "mode": item.get("mode", ""),
                "group_name": item.get("group_name", ""),
                "stream_name": item.get("stream_name", ""),
                "source_path": item.get("source_path", ""),
                "ts_unix": item.get("ts_unix"),
                "text_snippet": _text_snippet(item.get("text_snippet")),
            }
        )
    payload = {
        "n_total": int(getattr(resp, "cnt_total", len(source)) or 0),
        "execution_time_ms": getattr(resp, "execution_time_ms", 0),
        "data": rows,
        "trimmed": not verbose,
    }
    if not verbose:
        payload["n_total_returned"] = len(rows)
    return payload


def trim_jobs(resp: IndexationJobsListResponse) -> Dict[str, Any]:
    source = []
    if hasattr(resp, "data"):
        source = getattr(resp, "data") or []
    if not isinstance(source, list):
        source = []
    rows = []
    for item in source:
        if hasattr(item, "model_dump"):
            item = item.model_dump(exclude_none=True)
        if not isinstance(item, dict):
            item = {}
        rows.append(
            {
                "job_id": item.get("job_id", ""),
                "status": item.get("status", ""),
                "mode": item.get("mode", ""),
                "created_at": item.get("created_at"),
                "progress": item.get("progress"),
            }
        )
    return {"data": rows, "total": int(getattr(resp, "total", len(rows)) or 0)}
