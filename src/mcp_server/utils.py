from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
from src.utils.util_log import log_info, log_error, log_trace, log_warning


def obj_dict(value: Any) -> Dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    return dict(value) if isinstance(value, dict) else {}


def int_version_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if text.startswith("v"):
        text = text[1:]
    if not text.isascii() or not text.isdigit():
        raise ValueError("version must be a non-negative integer or vN")
    return int(text)


def list_versions(group: Dict[str, Any]) -> List[int]:
    out = set()
    for value in group.get("lancedb_versions") or []:
        try:
            version = int_version_id(value)
        except ValueError:
            continue
        if version is not None:
            out.add(version)
    return sorted(out, reverse=True)


def md_table(rows: List[Dict[str, Any]], columns: Dict[str, str]) -> str:
    def str_cell(value):
        if isinstance(value, list):
            value = ", ".join(str(x) for x in value)
        return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    lines = ["| " + " | ".join(columns.values()) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(str_cell(row.get(key)) for key in columns) + " |" for row in rows)
    return "\n".join(lines)


def collection_listing(resp: Any, subcollections: bool = False, collection_name: str = "", mode: Optional[str] = None) -> Dict[str, Any]:
    payload = obj_dict(resp)
    source = payload.get("rows", payload.get("data", [])) if subcollections else payload.get("data", [])
    rows = {}
    for raw in source or []:
        item = obj_dict(raw)
        group = str(item.get("group_name") or "").strip()
        item_mode = str(item.get("mode") or "").strip()
        stream = str(item.get("stream_name") or "").strip()
        if not group or (collection_name and group != collection_name) or (mode and item_mode != mode):
            continue
        if subcollections and not stream:
            continue
        row = {"collection_name": group, "mode": item_mode}
        if subcollections:
            row["sub_collection_name"] = stream
        else:
            row["lancedb_versions"] = [f"v{x}" for x in list_versions(item)]
        rows[(item_mode, group, stream if subcollections else "")] = row
    data = [rows[key] for key in sorted(rows)]
    columns = {"collection_name": "Collection"}
    if subcollections:
        columns["sub_collection_name"] = "Sub-collection"
    columns["mode"] = "Mode"
    if not subcollections:
        columns["lancedb_versions"] = "Index versions"
    return {"data": data, "total": len(data), "table": md_table(data, columns)}


def bool_missing_index(exc: Any) -> bool:
    text = str(exc.details or exc.body or exc).lower()
    index = any(x in text for x in ("lancedb", "image index", "img_emb"))
    missing = any(x in text for x in ("missing", "not found", "does not exist", "no such file", "no tablename resolved", "unable to resolve query embedding model"))
    return exc.status_code in (404, 500) and index and missing
