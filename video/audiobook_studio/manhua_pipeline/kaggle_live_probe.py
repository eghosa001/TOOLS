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
    ApiListKernelSessionOutputRequest, ApiGetKernelRequest,
)

STAGES = {
    "narration": re.compile(r"MANHUA_RYAN_PROGRESS\s+(\d+)\s+(\d+)"),
    "illustrations": re.compile(r"MANHUA_ART_PROGRESS\s+(\d+)\s+(\d+)"),
    "checkpoint": re.compile(r"MANHUA_PRIVATE_PROGRESS_SAVED\s+([a-z-]+)\s+(\d+)\s+(\d+)"),
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
    slug = os.environ.get("MANHUA_KAGGLE_SLUG", "private-eternal-dao-episode-1-manhua-assets")
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
    # Kaggle's metadata identifies the allocated GPU *machine shape*, not
    # whether a second GPU is idle inside the active worker process.
    try:
        resource_request = ApiGetKernelRequest()
        resource_request.user_name, resource_request.kernel_slug = owner, slug
        kernel = api.get_kernel(resource_request)
        meta = kernel.metadata
        if meta is None:
            raise RuntimeError("Missing notebook metadata")
        print("PRIVATE_EP01_ACCELERATOR_METADATA", json.dumps({
            "machine_shape": meta.machine_shape,
            "enable_gpu": meta.enable_gpu,
            "enable_tpu": meta.enable_tpu,
            "notebook_private": meta.is_private,
        }), flush=True)
    except Exception as e:
        print("PRIVATE_EP01_ACCELERATOR_METADATA_UNAVAILABLE", type(e).__name__, flush=True)


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

    if status == "ERROR":
        # Parse nested JSON-encoded session logs; reveal ONLY traceback function
        # names, library basename and redacted error category. No story/prompt text.
        import hashlib
        raw = result.log if output_info.get("available") else ""
        frames=[]
        for value in texts(raw):
            decoded=value.replace(chr(92)+"n",chr(10)).replace(chr(92)+'"', '"')
            frames.extend(re.findall(r'File "([^"\\n]+)", line (\\d+), in ([A-Za-z0-9_<>]+)',decoded))
        safe_frames=[]
        for location,number,func in frames[-12:]:
            base=os.path.basename(location)
            safe_frames.append({"file":base[:60],"line":int(number),"function":func[:70]})
        # Avoid disclosing the actual ValueError text, which may embed private story excerpts.
        signatures=[(key,key.lower() in raw.lower()) for key in (
            "token indices sequence length", "must have the same dtype",
            "invalid image prompt", "missing required", "expected scalar",
            "unsupported operand", "empty range", "NoneType",
            "IndexError", "TypeError", "not enough values to unpack",
            "too many values to unpack", "negative prompt",
            "invalid prompt", "tensor shapes", "attention_mask",
            "maximum sequence length", "Input type",
            "temperature", "sequence length", "image encoder",
            "selected indices")]
        expanded=raw
        for _ in range(4):
            expanded=expanded.replace(chr(92)+"n",chr(10)).replace(chr(92)+'"', '"')
        rec=[]
        for loc,num,func in re.findall(r'File "([^"\\n]+)", line (\\d+), in ([A-Za-z0-9_<>]+)',expanded):
            rec.append({"file":os.path.basename(loc)[:50],"line":int(num),"function":func[:60]})
        last_error=re.findall(r'(?:ValueError|RuntimeError|TypeError):\\s*([^\\n]{1,800})',expanded)
        brief=""
        if last_error:
            candidate=last_error[-1]
            candidate=re.sub(r"(['\\"]).*?\\1","[REDACTED]",candidate)
            brief=re.split(r'\\[|\\{',candidate)[0][:180]
        print("PRIVATE_EP01_SAFE_EXCEPTION_CONTEXT",json.dumps({
            "raw_is_json":raw.lstrip().startswith(("{","[")),
            "file_keyword_present":"File " in raw,
            "expanded_file_keyword_present":"File " in expanded,
            "frames":rec[-8:],"message_prefix_redacted":brief,
            "message_identified":bool(last_error)}),flush=True)
        print("PRIVATE_EP01_REDACTED_FAILURE_FRAMES",json.dumps({
            "frames":safe_frames,"signature_sha256":hashlib.sha256(raw.encode()).hexdigest()[:16],
            "keywords":[k for k,yes in signatures if yes]}),flush=True)


    # Report only a privacy-safe diagnosis; never copy prompts, story lines,
    # full tracebacks, or private output into public Actions logs.
    if status == "ERROR" and result.log:
        failure_log=result.log
        fingerprints={
            "ip_adapter": "ip_adapter" in failure_log.lower(),
            "reference_image": "reference_image" in failure_log.lower(),
            "cuda_out_of_memory": "out of memory" in failure_log.lower(),
            "image_dimensions": "size mismatch" in failure_log.lower(),
            "scheduler": "scheduler" in failure_log.lower(),
            "negative_prompt": "negative_prompt" in failure_log.lower(),
            "input_device": "input type" in failure_log.lower() or "same device" in failure_log.lower(),
            "invalid_generator": "generator" in failure_log.lower(),
            "too_many_tokens": "token indices sequence length" in failure_log.lower(),
            "invalid_attention": "attention" in failure_log.lower(),
            "mismatched_embeddings": "embedding" in failure_log.lower(),
            "pipeline_error": "diffusers" in failure_log.lower(),
        }
        # Fixed, hard-coded errors only, and optional exception location for debugging
        stack_hits=re.findall(r'File "[^"\\n]+", line (\\d+), in ([A-Za-z0-9_]+)',failure_log)
        print("PRIVATE_EP01_SAFE_ERROR_DIAGNOSIS",json.dumps({
            "class":"ValueError" if "ValueError" in failure_log else "OTHER",
            "fingerprints":fingerprints,"stack_functions":[name for _,name in stack_hits[-8:]],
            "traceback_lines":len(stack_hits),
        }),flush=True)


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
    # Recognize common SDXL failures from the full private output log without
    # printing its potentially sensitive exception text or manuscript content.
    # The previous probe only matched bare traceback lines; Kaggle may JSON-escape them.
    private_text = "\\n".join(str(v) for v in lines)
    private_text = private_text.replace("\\\\n", "\\n")
    patterns = {
        "clip_prompt_exceeds_context": r"(?:token indices sequence length|longer than the specified maximum sequence length|77 tokens)",
        "clip_attention_mask_shape": r"(?:attention_mask|attention mask).*(?:shape|size|dimension|length)",
        "ip_adapter_embedding_shape": r"(?:ip_adapter|image_embeds|image embeddings).*(?:shape|size|dimension|length)",
        "invalid_image_input": r"(?:ip_adapter_image|image encoder).*(?:invalid|not supported|missing|expected)",
        "value_error_with_tensor_mismatch": r"(?:ValueError|RuntimeError).*(?:tensor|matmul|matrix).*(?:size|shape|dimension)",
        "incompatible_image_encoder": r"(?:CLIPVisionModel|CLIPImageProcessor|image_encoder).*(?:expected|invalid|mismatch)",
        "gpu_out_of_memory": r"(?:CUDA out of memory|OutOfMemoryError)",
        "negative_prompt_length_mismatch": r"(?:negative.prompt).*(?:length|size|shape|tokens)",
        "cross_attention_kwargs": r"cross_attention_kwargs",
        "missing_conditioning": r"(?:prompt_embeds|negative_prompt_embeds).*(?:missing|must|expected)",
        "safety_checker": r"safety_checker",
        "invalid_argument_value": r"(?:ValueError:|value error)",
    }
    print("PRIVATE_EP01_SAFE_ROOT_CAUSE_SIGNATURES", json.dumps({
        "detected": [k for k,v in patterns.items() if re.search(v,private_text,re.I|re.S)],
        "output_log_length":len(private_text),
    }),flush=True)

    print("PRIVATE_EP01_LIVE_LOG_ENDPOINT", json.dumps(live), flush=True)
    print("PRIVATE_EP01_VERIFIED_STAGE_EVENTS", json.dumps(summarize(lines)), flush=True)
    # Extract only diagnostic exception lines; never print unpublished story text,
    # prompts, file paths, or arbitrary traceback lines.
    safe_errors = []
    for blob in lines:
        for value in texts(blob):
            for row in value.splitlines():
                match = re.match(r"^\\s*(ValueError|RuntimeError|TypeError|OutOfMemoryError|ImportError|KeyError):\\s*(.*)$", row)
                if not match:
                    continue
                msg = match.group(2)
                # Only report generic, known technical categories, not arbitrary
                # exception messages that might embed manuscript/prompt content.
                patterns = {
                    "ip_adapter_image_size_mismatch": r"ip.adapter.*(size|shape|dimension|embed)",
                    "torch_tensor_shape_mismatch": r"(tensor|matmul|matrix).*(shape|size|dimension)",
                    "diffusers_missing_image_encoder": r"image.encoder.*(missing|not found|load)",
                    "model_input_type_mismatch": r"Input type.*weight type",
                    "gpu_memory_exhaustion": r"(CUDA out of memory|allocate.*memory)",
                    "missing_image_reference": r"(image|reference).*(not found|missing)",
                    "invalid_inference_parameters": r"(height|width|inference_steps|guidance_scale).*(invalid|must)",
                }
                labels = [k for k,pat in patterns.items() if re.search(pat,msg,re.I)]
                safe_errors.append({"type":match.group(1),
                                    "categories":labels or ["unclassified_exception_message_redacted"]})
    print("PRIVATE_EP01_SAFE_EXCEPTION_DIAGNOSTICS",
          json.dumps(safe_errors[-4:]),flush=True)
    if not lines or not any(x in str(lines) for x in SAFE_MARKERS):
        print("PRIVATE_EP01_PROGRESS_UNVERIFIED_NO_STAGE_EVENTS", flush=True)


if __name__ == "__main__":
    run()
