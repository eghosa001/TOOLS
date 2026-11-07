"""Inspect private Kaggle live episode progress without exposing fiction or raw logs.

Uses Kaggle's live session SSE endpoint, unlike the CLI 'kernels logs' command,
which can return an empty result while a GPU session is running.
"""
from __future__ import annotations
import json
import os
import re
import signal
import sys
from collections import Counter

from kagglesdk import KaggleClient
from kagglesdk.kernels.types.kernels_api_service import (
    ApiGetKernelSessionLogsStreamRequest, ApiGetKernelSessionStatusRequest,
    ApiListKernelSessionOutputRequest,
)

STAGES = {
    "narration": re.compile(r"MANHUA_RYAN_PROGRESS\\s+(\\d+)\\s+(\\d+)"),
    "illustrations": re.compile(r"MANHUA_ART_PROGRESS\\s+(\\d+)\\s+(\\d+)"),
    "checkpoint": re.compile(r"MANHUA_PRIVATE_PROGRESS_SAVED\\s+([a-z-]+)\\s+(\\d+)\\s+(\\d+)"),
}
ERROR_NAMES = ("ModuleNotFoundError", "OutOfMemoryError", "ImportError",
               "SyntaxError", "RuntimeError", "ValueError", "KeyError",
               "PermissionError", "Traceback")
SAFE_MARKERS = (
    "MANHUA_IMAGE_MEMORY_MODE", "MANHUA_RYAN_PROGRESS",
    "MANHUA_ART_PROGRESS", "MANHUA_PRIVATE_PROGRESS_SAVED",
    "PRIVATE_D03_EP01_RESTART_RESULT", "MANHUA_VISUAL_QA",
    "MANHUA_TARGETED_ART_RETAKE", "PRIVATE_EP01_GPU_ASSET_RESULT",
)


def texts(blob, depth=0):
    """Extract only strings for stage detection, never publish source text."""
    if depth > 5:
        return
    if isinstance(blob, str):
        if blob.lstrip().startswith("{"):
            try:
                yield from texts(json.loads(blob), depth + 1)
                return
            except ValueError:
                pass
        yield blob[:4000]
    elif isinstance(blob, list):
        for value in blob[:60]:
            yield from texts(value, depth + 1)
    elif isinstance(blob, dict):
        for value in list(blob.values())[:25]:
            yield from texts(value, depth + 1)


def summarize(lines):
    progress = {}
    errors = set()
    safe_event_count = 0
    for raw in lines:
        for text in texts(raw):
            for name, pattern in STAGES.items():
                for match in pattern.finditer(text):
                    vals = match.groups()
                    if name == "checkpoint":
                        progress[name] = {"stage": vals[0], "completed": int(vals[1]),
                                          "total": int(vals[2])}
                    else:
                        progress[name] = {"completed": int(vals[0]), "total": int(vals[1])}
                    safe_event_count += 1
            for error in ERROR_NAMES:
                if error in text:
                    errors.add(error)
            if any(x in text for x in SAFE_MARKERS):
                safe_event_count += 1
    return {"progress": progress, "safe_event_count": safe_event_count,
            "error_types": sorted(errors)}


def run():
    token = os.environ.get("KAGGLE_API_TOKEN", "")
    owner = os.environ.get("KAGGLE_USERNAME", "aighewieghosa")
    slug = "private-eternal-dao-episode-1-manhua-assets"
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]+", owner):
        raise SystemExit("NO_PRIVATE_KAGGLE_AUTH")
    api = KaggleClient(api_token=token).kernels.kernels_api_client
    status = "UNKNOWN"
    try:
        request = ApiGetKernelSessionStatusRequest()
        request.user_name, request.kernel_slug = owner, slug
        result = api.get_kernel_session_status(request)
        status = getattr(result.status, "name", None) or str(result.status).split(".")[-1]
    except Exception as e:
        print("KAGGLE_SDK_STATUS_ERROR", type(e).__name__, flush=True)
    print("PRIVATE_EP01_CURRENT_STATE", status, flush=True)

    lines = []
    output_info = {"available": False, "file_counts_by_extension": {}}
    try:
        request = ApiListKernelSessionOutputRequest()
        request.user_name, request.kernel_slug = owner, slug
        request.page_size = 100
        result = api.list_kernel_session_output(request)
        lines.append(result.log or "")
        counts = Counter(os.path.splitext(f.file_name)[1].lower() for f in (result.files or []))
        output_info = {"available": True, "log_chars": len(result.log or ""),
                       "file_counts_by_extension": dict(counts),
                       "has_more_files": bool(result.next_page_token)}
    except Exception as e:
        output_info["failure_type"] = type(e).__name__
    print("PRIVATE_EP01_OUTPUT_API", json.dumps(output_info), flush=True)

    live = {"called": False, "received_event_count": 0, "content_type": "UNKNOWN"}
    response = None
    def timeout_handler(*unused):
        raise TimeoutError("bounded live log read completed")
    prior = signal.signal(signal.SIGALRM, timeout_handler)
    try:
        request = ApiGetKernelSessionLogsStreamRequest()
        request.user_name, request.kernel_slug = owner, slug
        request.wait_for_logs_url_seconds = 2
        signal.alarm(16)
        response = api.get_kernel_session_logs_stream(request)
        live["called"] = True
        live["content_type"] = response.headers.get("Content-Type", "UNKNOWN").split(";")[0]
        for line in response.iter_lines(chunk_size=1024, decode_unicode=True):
            if line:
                live["received_event_count"] += 1
                if line.startswith("data:"):
                    lines.append(line[5:][:4000])
                elif live["content_type"] == "application/json":
                    lines.append(line[:4000])
            if live["received_event_count"] >= 250:
                break
    except (TimeoutError, OSError) as e:
        live["result"] = type(e).__name__
    except Exception as e:
        live["result"] = type(e).__name__
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prior)
        if response:
            response.close()
    print("PRIVATE_EP01_LIVE_LOG_ENDPOINT", json.dumps(live), flush=True)
    print("PRIVATE_EP01_VERIFIED_STAGE_EVENTS", json.dumps(summarize(lines)), flush=True)
    if not lines or not any(x in str(lines) for x in SAFE_MARKERS):
        print("PRIVATE_EP01_PROGRESS_UNVERIFIED_NO_STAGE_EVENTS", flush=True)


if __name__ == "__main__":
    run()
