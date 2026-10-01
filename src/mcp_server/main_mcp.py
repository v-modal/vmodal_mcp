from typing import Any, Dict, Optional, Literal
import os
import sys
import base64
import json
import fire
import inspect
import asyncio
import hashlib
from contextlib import asynccontextmanager

os.environ.setdefault("VMODAL_AUTH_CACHE_DIR", "ztmp/vmodal_auth")

from mcp.server.fastmcp import FastMCP
from vmodal import Client
from vmodal.errors import SdkError, AuthError, ApiError, ValidationFailed
from src.utils.util_log import log_info, log_error, log_trace, log_warning
from src.mcp_server.registry import TOOL_REGISTRY, tool_schema
from src.mcp_server.config import McpConfig

_ACTIVE_CFG: Optional[McpConfig] = None
_ACTIVE_CLIENT: Optional[Client] = None
_TARGET_CACHE: Dict[str, Any] = {}

def _json_type_to_py(py_prop: Dict[str, Any]) -> Any:
    if "anyOf" in py_prop:
        non_null = [x for x in py_prop["anyOf"] if (x or {}).get("type") != "null"]
        if len(non_null) == 1:
            return _json_type_to_py(non_null[0])
    ptype = py_prop.get("type")
    if isinstance(ptype, list):
        non_null = [x for x in ptype if x != "null"]
        if len(non_null) == 1:
            return _json_type_to_py({"type": non_null[0]})
    if ptype == "string":
        return str
    if ptype == "integer":
        return int
    if ptype == "number":
        return float
    if ptype == "boolean":
        return bool
    if ptype == "array":
        values = (py_prop.get("items") or {}).get("enum")
        if values:
            return list[Literal[tuple(values)]]
        return list[Any]
    if ptype == "object":
        return dict
    return Any


def _build_signature(schema: Dict[str, Any]) -> inspect.Signature:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []) or [])
    req_params = []
    opt_params = []
    for key, value in properties.items():
        ann = _json_type_to_py(value if isinstance(value, dict) else {})
        if key in required:
            default = inspect.Parameter.empty
        else:
            default = value.get("default") if isinstance(value, dict) else inspect.Parameter.empty
        param = inspect.Parameter(
            name=key,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=ann,
            default=default,
        )
        if key in required:
            req_params.append(param)
        else:
            opt_params.append(param)
    return inspect.Signature(req_params + opt_params)

def _os_mkdirs(path: str):
    if path:
        os.makedirs(path, exist_ok=True)


def _safe_name(s: str) -> str:
    base = os.path.basename(str(s or "").strip())
    out = "".join(c if c.isalnum() or c in "._-" else "_" for c in base)
    out = out.strip("._") or "x"
    return out[:80]


def _sniff_ext(raw: bytes) -> str:
    """Detect the real image extension from magic bytes; the backend can return
    webp/png/etc, not just jpeg (image uploads get converted server-side)."""
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if raw[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    if raw[:2] == b"BM":
        return ".bmp"
    return ".jpg"


def _os_dir_cap(dirpath: str, max_files: int = 500):
    if not dirpath or not os.path.isdir(dirpath):
        return
    files = [os.path.join(dirpath, f) for f in os.listdir(dirpath)]
    files = [f for f in files if os.path.isfile(f)]
    if len(files) <= max_files:
        return
    files.sort(key=lambda f: os.path.getmtime(f))  # oldest first
    for f in files[: len(files) - max_files]:
        try:
            os.remove(f)
        except Exception:
            pass


def _coerce_dict(value: Any) -> Dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if isinstance(value, dict):
        return dict(value)
    return {}


def _str_tool_error(exc: Exception) -> Dict[str, Any]:
    if isinstance(exc, AuthError):
        detail = getattr(exc, "details", None) or getattr(exc, "body", None) or str(exc)
        return {
            "error_type": "AuthError",
            "status_code": int(getattr(exc, "status_code", 401) or 401),
            "detail": detail or "Bearer token required",
        }
    if isinstance(exc, ValidationFailed):
        return {
            "error_type": "ValidationFailed",
            "status_code": int(getattr(exc, "status_code", 422) or 422),
            "detail": getattr(exc, "details", None) or str(exc),
        }
    if isinstance(exc, ApiError):
        return {
            "error_type": "ApiError",
            "status_code": int(getattr(exc, "status_code", 500) or 500),
            "detail": getattr(exc, "details", None) or str(exc),
        }
    if isinstance(exc, Exception):
        return {
            "error_type": exc.__class__.__name__,
            "status_code": 500,
            "detail": str(exc),
        }
    return {"error_type": "Error", "status_code": 500, "detail": str(exc)}


@asynccontextmanager
async def _lifespan(server: FastMCP):
    config = _ACTIVE_CFG
    if not isinstance(config, McpConfig):
        config = McpConfig.from_env()
    max_files = int(str(os.environ.get("MCP_IMAGE_MAX_FILES") or "500") or 500)
    _os_dir_cap(config.image_dir, max_files=max_files)
    client = Client(cfg=config.sdk)
    global _ACTIVE_CLIENT
    _ACTIVE_CLIENT = client
    _TARGET_CACHE.clear()  # fresh client → drop stale bound methods
    try:
        # async with already closes the client on exit
        async with client:
            yield
    finally:
        _ACTIVE_CLIENT = None
        _TARGET_CACHE.clear()


def _resolve_target(client: Client, target: str):
    cached = _TARGET_CACHE.get(target)
    if cached is not None:
        return cached
    method_fix = {
        "description_update": "update_description",
    }
    obj = client
    for part in target.split("."):
        method = getattr(obj, part, None)
        if method is None and part in method_fix:
            method = getattr(obj, method_fix[part], None)
        if method is None:
            raise RuntimeError(f"tool target not found: {target}")
        obj = method
    _TARGET_CACHE[target] = obj
    return obj


def _tool_payload(payload: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if len(payload) == 1:
        key = next(iter(payload.keys()))
        if key not in schema.get("properties", {}):
            wrapped = payload[key]
            if isinstance(wrapped, dict):
                return wrapped
    return payload


async def _tool_output(
    resp: Any,
    spec: Dict[str, Any],
    *,
    verbose: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    if spec.get("trim"):
        if spec.get("target") == "searches.search_video":
            resp = spec["trim"](resp, verbose=verbose, context=context)
        else:
            resp = spec["trim"](resp)
    if spec.get("is_image"):
        cfg = _ACTIVE_CFG
        if not isinstance(cfg, McpConfig):
            raise RuntimeError(_tool_error(RuntimeError("missing server config")))
        handler = spec.get("handler", "")
        # offload blocking file IO + b64decode off the event loop
        if handler == "image_bulk":
            payload = await asyncio.to_thread(_tool_image_bulk_output, resp, cfg)
        else:
            payload = await asyncio.to_thread(_tool_image_output, resp, cfg, handler)
        return json.dumps(payload, ensure_ascii=False)
    if hasattr(resp, "model_dump"):
        payload = resp.model_dump(exclude_none=True)
    elif isinstance(resp, (dict, list, str, int, float, bool)) or resp is None:
        payload = resp
    else:
        payload = {"result": str(resp)}
    return json.dumps(payload, ensure_ascii=False)


def _ensure_client() -> Client:
    if _ACTIVE_CLIENT is None:
        raise RuntimeError("mcp server lifecycle not initialized")
    return _ACTIVE_CLIENT


def _tool_error(error: SdkError) -> str:
    return json.dumps(_str_tool_error(error))


def _validation_error(detail: Any) -> RuntimeError:
    return RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": detail}))


def _apply_call_contract(data: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(data)
    for key, value in (spec.get("call_defaults") or {}).items():
        if key not in data or (data.get(key) is None and key in (spec.get("call_defaults_null") or [])):
            data[key] = value
    missing = [key for key in spec.get("required_nonempty") or [] if not str(data.get(key) or "").strip()]
    if missing:
        raise _validation_error({"missing_fields": missing})
    transform = spec.get("input_transform")
    if transform:
        key = spec.get("input_transform_key") or "records"
        try:
            data[key] = transform(data.get(key))
        except ValueError as exc:
            detail = exc.args[0] if exc.args else str(exc)
            raise _validation_error(detail)
    return data


def _str_search_error(exc: SdkError) -> str:
    payload = _str_tool_error(exc)
    detail = payload.get("detail")
    text = str(detail or "").lower()
    if any(key in text for key in ["img_emb", "image index", "lancedb", "table", "version"]):
        hint = "Call collection_groups_list(mode=...) and retry with an explicit version_lancedb."
        payload["detail"] = f"{detail} {hint}" if detail else hint
    return json.dumps(payload)


def _check_upload_path(path: str, cfg: McpConfig) -> str:
    if not str(path or "").strip():
        raise RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": "missing file_path"}))
    file_path = str(path).strip()
    if not os.path.isfile(file_path):
        raise RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": f"missing file: {file_path}"}))
    max_bytes = int(cfg.upload_max_mb) * 1024 * 1024
    if os.path.getsize(file_path) > max_bytes:
        raise RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": f"file too large: > {cfg.upload_max_mb}MB"}))
    return file_path


def _check_upload_folder(path: str) -> str:
    if not str(path or "").strip():
        raise RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": "missing folder_path"}))
    folder_path = str(path).strip()
    if not os.path.isdir(folder_path):
        raise RuntimeError(json.dumps({"error_type": "ValidationError", "status_code": 422, "detail": f"missing folder: {folder_path}"}))
    return folder_path


def _write_image_file(payload: Dict[str, Any], cfg: McpConfig, default_name: str, unique: bool = False) -> Dict[str, Any]:
    data = _coerce_dict(payload)
    if isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)
    else:
        text = str(data.get("img_base64") or data.get("content_base64") or "")
        raw = b""
        if text:
            try:
                raw = base64.b64decode(text, validate=False)
            except Exception:
                meta = _coerce_dict(payload)
                meta.pop("img_base64", None)
                meta.pop("content_base64", None)
                return {"saved_path": "", "n_bytes": 0, "error": "bad base64", "meta": meta}
    if not raw:
        meta = _coerce_dict(payload)
        meta.pop("img_base64", None)
        meta.pop("content_base64", None)
        return {"saved_path": "", "n_bytes": 0, "meta": meta}
    meta = _coerce_dict(payload)
    meta.pop("img_base64", None)
    meta.pop("content_base64", None)
    _os_mkdirs(cfg.image_dir)
    base = os.path.splitext(default_name)[0] or "image"
    if unique:
        base = f"{base}_{hashlib.sha256(raw).hexdigest()[:12]}"
    name = f"{base}{_sniff_ext(raw)}"
    path = os.path.join(cfg.image_dir, name)
    with open(path, "wb") as f:
        f.write(raw)
    return {"saved_path": path, "n_bytes": len(raw), "meta": meta}


def _tool_image_output(payload: Any, cfg: McpConfig, handler_name: str) -> Dict[str, Any]:
    data = _coerce_dict(payload)
    if isinstance(payload, (bytes, bytearray)) or handler_name == "image_bytes":
        return _write_image_file(payload, cfg, "image.jpg", unique=True)
    if handler_name == "image_get":
        stream = _safe_name(data.get("stream_name") or "astream")
        frame = _safe_name(data.get("frame_id") or "frame")
        name = f"{stream}_{frame}.jpg"
        return _write_image_file(data, cfg, name)
    if handler_name == "image_get_fullpath":
        fullpath = data.get("fullpath", "image")
        base = os.path.splitext(_safe_name(fullpath))[0] or "image"
        name = f"{base}.jpg"
        return _write_image_file(data, cfg, name)
    return {"saved_path": "", "n_bytes": 0, "meta": data}


def _tool_image_bulk_output(payload: Any, cfg: McpConfig) -> Dict[str, Any]:
    data = _coerce_dict(payload)
    items = data.get("records")
    if not isinstance(items, list):
        items = []
    skipped = max(0, len(items) - 20)
    out = []
    for idx, item in enumerate(items[:20]):
        item_data = _coerce_dict(item)
        frame = _safe_name(item_data.get("frame_id") or str(idx))
        stream = _safe_name(item_data.get("stream_name") or "astream")
        name = f"{stream}_{frame}.jpg"
        out.append(_write_image_file(item_data, cfg, name))
    return {"saved_paths": [x["saved_path"] for x in out], "skipped": skipped}


def _build_handler(name: str, spec: Dict[str, Any]):
    target = spec["target"]
    schema = tool_schema(spec)
    if target == "searches.search_video":
        if "verbose" not in schema.get("properties", {}):
            schema = dict(schema)
            props = dict(schema.get("properties", {}))
            props["verbose"] = {"type": "boolean", "title": "Verbose", "default": False}
            schema["properties"] = props
    handler_name = spec.get("handler") or name

    async def _handler(**payload):
        log_trace("tool", name)
        cfg = _ACTIVE_CFG
        if not isinstance(cfg, McpConfig):
            raise RuntimeError("mcp server lifecycle not initialized")
        if cfg and cfg.cfg_error:
            raise RuntimeError(json.dumps({"error_type": "AuthError", "status_code": 401, "detail": cfg.cfg_error}))
        data = _tool_payload(payload, schema)
        data = _apply_call_contract(data, spec)
        if spec.get("is_upload"):
            key = spec.get("upload_path_key") or "path"
            file_path = _check_upload_path(data.get(key, ""), cfg)
            data[key] = file_path
        if spec.get("is_upload_folder"):
            key = spec.get("upload_folder_key") or "folderpath_local"
            data[key] = _check_upload_folder(data.get(key, ""))
        verbose = False
        context = None
        if target == "searches.search_video":
            verbose = bool(data.pop("verbose", False))
            context = {key: data.get(key) for key in ["mode", "group_name", "stream_name", "search_sources", "version_lancedb"]}
        client = _ensure_client()
        call = _resolve_target(client, target)
        try:
            if spec.get("long_running"):
                # SDK upload parts already have bounded timeouts and retry/resume.
                # An outer timeout would cancel a healthy large-file transfer.
                out = await call(**data)
            else:
                out = await asyncio.wait_for(call(**data), timeout=cfg.tool_timeout)
        except asyncio.TimeoutError:
            log_error("tool_fail", name, "timeout")
            raise RuntimeError(json.dumps({"error_type": "Timeout", "status_code": 504,
                                           "detail": f"tool timed out after {cfg.tool_timeout}s"}))
        except SdkError as exc:
            log_error("tool_fail", name, str(exc))
            if target == "searches.search_video":
                raise RuntimeError(_str_search_error(exc))
            raise RuntimeError(_tool_error(exc))
        out_spec = {**spec, "handler": handler_name}
        return await _tool_output(out, out_spec, verbose=verbose, context=context)

    _handler.__name__ = f"{name}_handler"
    _handler.__signature__ = _build_signature(schema)
    _handler.__doc__ = spec.get("desc", "")
    return _handler


def _register_tools(server: FastMCP):
    for name, spec in TOOL_REGISTRY.items():
        server.add_tool(
            _build_handler(name, spec),
            name=name,
            description=spec.get("desc"),
        )


def build_server(config: Optional[McpConfig] = None) -> FastMCP:
    cfg = config or McpConfig.from_env()
    global _ACTIVE_CFG
    _ACTIVE_CFG = cfg
    server = FastMCP(name="vmodal-mcp", lifespan=_lifespan)
    _register_tools(server)
    return server


def run(transport: str = "", port: int = 8199):
    cfg = McpConfig.from_env()
    cfg.transport = transport.strip().lower() or cfg.transport
    server = build_server(cfg)
    if cfg.transport == "http":
        server.run(transport="streamable-http", host="127.0.0.1", port=port)
    else:
        server.run()


def main() -> int:
    run()
    return 0


def cli() -> int:
    if len(sys.argv) == 1:
        return main()
    fire.Fire({"run": run, "main": main})
    return 0


if __name__ == "__main__":
    cli()
