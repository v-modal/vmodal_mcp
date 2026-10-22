from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire
import base64
import io
import json
import re
from pathlib import Path
from PIL import Image
from src.utils.util_log import log_info, log_error, log_trace, log_warning


def str_frame_component(value: Any) -> str:
    text = re.sub(r"[^\w.-]", "_", str(value or "").strip()).strip("._")
    if not text:
        raise ValueError("empty_path_component")
    return text


def os_frame_path(root: str, row: Dict[str, Any]) -> str:
    root = Path(root).expanduser().resolve()
    ts = str(row.get("ts_unix_13digits") or "")
    if not re.fullmatch(r"[0-9]{13}", ts):
        raise ValueError("invalid_timestamp")
    filename = str(row.get("filename") or "").replace("\\", "/").rsplit("/", 1)[-1]
    stem = str_frame_component(os.path.splitext(filename)[0])
    path = root / str_frame_component(row.get("group_name")) / str_frame_component(row.get("stream_name")) / f"{stem}_{ts}.jpg"
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("path_outside_root")
    return str(path)


def image_bytes(payload: Any) -> bytes:
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    data = obj_dict(payload)
    return base64.b64decode(data.get("img_base64") or data.get("content_base64") or "", validate=True)


def image_validate(raw: bytes) -> None:
    if not raw:
        raise ValueError("empty_image")
    with Image.open(io.BytesIO(raw)) as img:
        img.load()


def os_read_image(path: str) -> bytes:
    with open(os.path.expanduser(path), "rb") as fh:
        return fh.read()


def os_save_frame(payload: Any, path: str, record: Dict[str, Any]) -> Dict[str, Any]:
    raw = image_bytes(payload)
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        if img.format == "JPEG" and img.mode == "RGB":
            jpeg = raw
        else:
            rgb = Image.new("RGB", img.size, "white")
            rgba = img.convert("RGBA")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
            buf = io.BytesIO()
            rgb.save(buf, format="JPEG")
            jpeg = buf.getvalue()
    if not jpeg.startswith(b"\xff\xd8\xff"):
        raise ValueError("invalid_jpeg")
    # Exclusive creation also prevents overwriting a frame saved in an earlier call.
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # A sidecar distinguishes selectors that sanitize to the same deterministic name.
    owner_path = path + ".json"
    try:
        with open(owner_path, "x", encoding="utf-8") as fh:
            json.dump(record, fh, sort_keys=True)
    except FileExistsError:
        with open(owner_path, encoding="utf-8") as fh:
            if json.load(fh) != record:
                raise ValueError("path_conflict")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            if fh.read() != jpeg:
                raise ValueError("path_conflict")
    else:
        try:
            with open(path, "xb") as fh:
                fh.write(jpeg)
        except FileExistsError:
            with open(path, "rb") as fh:
                if fh.read() != jpeg:
                    raise ValueError("path_conflict")
    return {"saved_path": path, "n_bytes": len(jpeg)}


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
