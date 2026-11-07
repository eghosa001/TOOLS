#!/usr/bin/env python3
"""Private Kaggle T4x2 supervisor: queue approved episodes, run one per PHYSICAL GPU.

GitHub Actions appends to a PRIVATE Kaggle queue dataset. A single private
supervisor kernel polls it while running; it does not modify a running legacy
notebook. Each worker subprocess owns cuda:0 OR cuda:1 in the SAME runtime.
No private prose or media is published to GitHub.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from video.audiobook_studio.manhua_pipeline.core import VOICE, validate_slug

SCHEMA = "manhua-dual-t4-queue-v1"
DATASET = re.compile(r"^[A-Za-z0-9_-]+/[A-Za-z0-9_-]+$")
VALID_PHASES = ("assets", "review")
VALID_QUALITIES = ("fast", "quality")
WORK = Path(os.environ.get("MANHUA_DISPATCH_WORK", "/kaggle/working/manhua-dispatch"))


def checked_ref(value: str) -> str:
    if not DATASET.fullmatch(value):
        raise ValueError("Expected private Kaggle dataset owner/slug")
    return value


def key(task: dict) -> str:
    return f"{task['story_id']}:{task['episode']}:{task['source_sha256']}"


def task_record(*, story_id: str, episode: int, private_dataset: str,
                source_sha256: str, progress_dataset: str = "",
                phase: str = "assets", quality: str = "quality") -> dict:
    validate_slug(story_id)
    if not 1 <= int(episode) <= 999 or phase not in VALID_PHASES or quality not in VALID_QUALITIES:
        raise ValueError("Invalid episode, production phase or art quality")
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("Approved episode source SHA-256 is required")
    checked_ref(private_dataset)
    if progress_dataset:
        checked_ref(progress_dataset)
    return {"story_id": story_id, "episode": int(episode),
            "private_dataset": private_dataset, "source_sha256": source_sha256,
            "progress_dataset": progress_dataset, "phase": phase, "quality": quality,
            "voice_profile": VOICE}


def validate_task(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("voice_profile") != VOICE:
        raise ValueError("Incorrect approved Qwen Ryan profile")
    return task_record(**{x: data.get(x, "") for x in (
        "story_id", "episode", "private_dataset", "source_sha256",
        "progress_dataset", "phase", "quality")})


def enqueue(queue: dict, task: dict) -> tuple[dict, bool]:
    if queue.get("schema") != SCHEMA or not isinstance(queue.get("tasks"), list):
        raise ValueError("Unrecognized private queue data")
    task = validate_task(task)
    for existing in queue["tasks"]:
        prev = validate_task(existing)
        if prev["story_id"] == task["story_id"] and prev["episode"] == task["episode"]:
            if prev != task:
                raise ValueError("Episode already queued with a different approved source/settings")
            return queue, False
    queue["tasks"].append(task)
    return queue, True


def command(args: list[str], *, timeout: int = 180, allow_failure: bool = False):
    done = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if done.returncode and not allow_failure:
        # Never echo command stderr; private dataset or auth details could leak.
        raise RuntimeError(f"Kaggle operation failed: {args[1:3]}")
    return done


def get_dataset_json(ref: str, file_name: str) -> dict | None:
    """Read a single small PRIVATE file, not full source datasets."""
    checked_ref(ref)
    with tempfile.TemporaryDirectory() as folder:
        result = command(["kaggle", "datasets", "download", "-d", ref,
                          "-f", file_name, "-p", folder, "--force", "-q"],
                         timeout=180, allow_failure=True)
        if result.returncode:
            # Missing datasets are handled ONLY by callers explicitly creating one.
            return None
        path = Path(folder) / file_name
        if not path.is_file():
            raise RuntimeError("Private dataset did not return requested JSON")
        return json.loads(path.read_text())


def persist_dataset(ref: str, filename: str, data: dict, *, create: bool = False) -> None:
    """Write a small PRIVATE queue/results manifest. A single writer owns each ref."""
    checked_ref(ref)
    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder)
        (stage / filename).write_text(json.dumps(data, indent=2, sort_keys=True))
        (stage / "dataset-metadata.json").write_text(json.dumps({
            "id": ref, "title": "Private audiobook dispatch state",
            "licenses": [{"name": "CC0-1.0"}]}))
        if create:
            command(["kaggle", "datasets", "create", "-p", folder, "-q"], timeout=240)
        else:
            command(["kaggle", "datasets", "version", "-p", folder, "-q",
                     "-m", "Private studio dispatch state update"], timeout=240)


def verify_private_approval(task: dict) -> dict:
    """CPU gate BEFORE queueing: actual signed-in-package SHA and owner flags."""
    from video.audiobook_studio.manhua_pipeline import kaggle_runner
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        command(["kaggle", "datasets", "download", "-d", task["private_dataset"],
                 "-p", str(stage), "--unzip", "-q"], timeout=300)
        original_work = kaggle_runner.WORK
        original_dir = os.environ.get("MANHUA_INPUT_DIR")
        try:
            kaggle_runner.WORK = stage / "work"
            os.environ["MANHUA_INPUT_DIR"] = str(stage)
            package = kaggle_runner.find_source()
            from video.audiobook_studio.manhua_pipeline.core import open_package
            meta, script, _ = open_package(package, expected_story_id=task["story_id"],
                                           episode=task["episode"])
        finally:
            kaggle_runner.WORK = original_work
            if original_dir is None:
                os.environ.pop("MANHUA_INPUT_DIR", None)
            else:
                os.environ["MANHUA_INPUT_DIR"] = original_dir
        actual = meta["episodes"][task["episode"]-1]["sha256"]
        if task.get("source_sha256") and actual != task["source_sha256"]:
            raise ValueError("Private episode source differs from supplied SHA-256")
        if not meta.get("source_approved"):
            raise ValueError("Unapproved private story source")
        if not meta.get("image_model_rights_reviewed"):
            raise ValueError("Illustration model rights gate incomplete")
        briefs = (meta.get("scene_briefs") or {}).get(str(task["episode"]))
        if not isinstance(briefs, list) or not briefs or not all(
                isinstance(item, str) and item.strip() for item in briefs):
            raise ValueError("Approved episode scene/storyboard briefs are required")
        if not script.strip():
            raise ValueError("Empty approved narration script")
        return actual


def add_approved_task(queue_ref: str, task: dict) -> bool:
    actual_sha = verify_private_approval(task)
    task = validate_task({**task, "source_sha256": actual_sha})
    current = get_dataset_json(queue_ref, "queue.json")
    creating = current is None
    current = current if current is not None else {"schema": SCHEMA, "tasks": []}
    updated, added = enqueue(current, task)
    if added:
        persist_dataset(queue_ref, "queue.json", updated, create=creating)
    print("MANHUA_PRIVATE_QUEUE", "QUEUED" if added else "ALREADY_PRESENT",
          {"task_key_sha256": task["source_sha256"][:12], "episode": task["episode"]},
          flush=True)
    return added


def kaggle_secret() -> None:
    if os.environ.get("KAGGLE_API_TOKEN"):
        return
    from kaggle_secrets import UserSecretsClient
    token = UserSecretsClient().get_secret("MANHUA_KAGGLE_API_TOKEN")
    if not token:
        raise RuntimeError("Kaggle secret MANHUA_KAGGLE_API_TOKEN is not enabled")
    os.environ["KAGGLE_API_TOKEN"] = token


def pull_input(ref: str, dest: Path) -> Path:
    marker = dest / ".verified-download"
    if not marker.is_file():
        dest.mkdir(parents=True, exist_ok=True)
        command(["kaggle", "datasets", "download", "-d", checked_ref(ref),
                 "-p", str(dest), "--unzip", "-q"], timeout=900)
        marker.write_text(ref)
    return dest


def save_private_progress(ref: str, checkpoint: Path) -> None:
    """Each story/episode has its OWN reusable private Kaggle progress dataset."""
    checked_ref(ref)
    if not checkpoint.is_file():
        return
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        shutil.copy2(checkpoint, stage / "MANHUA_PROGRESS.zip")
        (stage / "dataset-metadata.json").write_text(json.dumps({
            "id": ref, "title": "Private audiobook episode checkpoint",
            "licenses": [{"name": "CC0-1.0"}]}))
        status = command(["kaggle", "datasets", "files", ref, "--csv"],
                         allow_failure=True)
        create = status.returncode != 0
        if create:
            command(["kaggle", "datasets", "create", "-p", str(stage), "-q"], timeout=900)
        else:
            command(["kaggle", "datasets", "version", "-p", str(stage), "-q",
                     "-m", "Approved-source-bound episode checkpoint"], timeout=900)


def progress_ref(owner: str, task: dict) -> str:
    # Kaggle slug is bounded and stable even for long story IDs.
    import hashlib
    token = hashlib.sha256(key(task).encode()).hexdigest()[:16]
    return f"{owner}/manhua-progress-{token}"


def start_worker(task: dict, slot: int, owner: str) -> dict:
    """Do not import torch/model globally. Give subprocess an isolated CUDA ID."""
    task = validate_task(task)
    if slot not in (0, 1):
        raise ValueError("Unsupported physical GPU slot")
    target = WORK / f"gpu{slot}" / task["story_id"] / f"ep{task['episode']:03}"
    input_dir = target / "private_input"
    progress_dir = target / "private_progress"
    pull_input(task["private_dataset"], input_dir)
    checkpoint_ref = task["progress_dataset"] or progress_ref(owner, task)
    # Missing checkpoint is fine for the first run, but invalid credentials are not.
    exists = command(["kaggle", "datasets", "files", checkpoint_ref, "--csv"],
                     allow_failure=True).returncode == 0
    if exists:
        pull_input(checkpoint_ref, progress_dir)
    env = os.environ.copy()
    env.update({
        "MANHUA_GPU_SLOT": str(slot),
        "MANHUA_WORK_DIR": str(target / "work"),
        "MANHUA_INPUT_DIR": str(input_dir),
        "MANHUA_PROGRESS_INPUT_DIR": str(progress_dir if exists else input_dir),
    })
    # Do not print private scripts, prompts, or subprocess logs into public CI.
    log = target / "private-worker.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    stream = log.open("ab")
    args = [sys.executable, "-m",
            "video.audiobook_studio.manhua_pipeline.kaggle_runner",
            "--story-id", task["story_id"], "--episode", str(task["episode"]),
            "--phase", task["phase"], "--quality", task["quality"]]
    try:
        process = subprocess.Popen(args, env=env, stdout=stream, stderr=subprocess.STDOUT)
    finally:
        stream.close()
    print("MANHUA_SLOT_START", {"gpu": slot, "task": key(task)[:48]}, flush=True)
    return {"task": task, "process": process, "slot": slot, "work": target,
            "progress_ref": checkpoint_ref, "tries": 1}


def supervise(queue_ref: str, results_ref: str, owner: str, *, poll_seconds: int = 45,
              idle_polls: int = 3, retry_limit: int = 1) -> dict:
    """Single-runtime scheduler. Each failure affects only its GPU subprocess."""
    kaggle_secret()
    checked_ref(queue_ref)
    checked_ref(results_ref)
    checked_ref(owner + "/check")
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
        raise RuntimeError("PHYSICAL T4x2 NOT AVAILABLE: refuse to claim GPU1")
    print("MANHUA_PHYSICAL_T4X2_READY", torch.cuda.device_count(), flush=True)
    record = get_dataset_json(results_ref, "results.json")
    create_record = record is None
    record = record or {"schema": SCHEMA, "completed": {}, "blocked": {}}
    if (record.get("schema") != SCHEMA
            or not isinstance(record.get("completed"), dict)
            or not isinstance(record.get("blocked", {}), dict)):
        raise RuntimeError("Invalid durable private completion registry")
    record.setdefault("blocked", {})
    finished = set(record["completed"])
    blocked = set(record["blocked"])
    active: dict[int, dict] = {}
    attempted: set[str] = set()
    last_tasks = []
    pending_persist = False
    quiet = 0
    failures_to_poll = 0
    while True:
        try:
            remote = get_dataset_json(queue_ref, "queue.json")
            if remote is None or remote.get("schema") != SCHEMA:
                raise RuntimeError("Private queue inaccessible or invalid")
            tasks = [validate_task(t) for t in remote["tasks"]]
            if len({(t["story_id"], t["episode"]) for t in tasks}) != len(tasks):
                raise RuntimeError("Duplicate story/episode in private queue")
            last_tasks = tasks
            failures_to_poll = 0
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            failures_to_poll += 1
            print("MANHUA_QUEUE_POLL_RETRY_NO_GPU_INTERRUPTION",
                  type(exc).__name__, flush=True)
            tasks = last_tasks
            if not active and failures_to_poll >= 5:
                raise RuntimeError("Cannot read approved private queue; no GPU launched") from exc
        for slot, job in list(active.items()):
            ret = job["process"].poll()
            if ret is None:
                continue
            active.pop(slot)
            task = job["task"]
            checkpoint = job["work"] / "work" / "MANHUA_PROGRESS.zip"
            persisted = True
            try:
                save_private_progress(job["progress_ref"], checkpoint)
            except Exception as exc:
                persisted = False
                print("MANHUA_PROGRESS_PERSIST_FAILED",
                      {"gpu": slot, "type": type(exc).__name__}, flush=True)
            if ret == 0:
                record["completed"][key(task)] = {
                    "gpu": slot, "state": "PRIVATE_REVIEW_ONLY",
                    "checkpoint_persisted": persisted}
                finished.add(key(task))
                pending_persist = True
                print("MANHUA_SLOT_DONE", {"gpu": slot, "episode": task["episode"]}, flush=True)
            elif job["tries"] <= retry_limit:
                try:
                    print("MANHUA_SLOT_RETRY_ONLY_THIS_WORKER", {"gpu": slot}, flush=True)
                    restarted = start_worker(task, slot, owner)
                    restarted["tries"] = job["tries"] + 1
                    active[slot] = restarted
                except Exception as exc:
                    record["blocked"][key(task)] = {"gpu": slot,
                        "reason": type(exc).__name__, "state": "FAILED_REQUIRES_REVIEW"}
                    blocked.add(key(task))
                    pending_persist = True
                    print("MANHUA_SLOT_RETRY_SETUP_FAILED", {"gpu": slot}, flush=True)
            else:
                record["blocked"][key(task)] = {
                    "gpu": slot, "reason": "WORKER_EXIT_NONZERO",
                    "state": "FAILED_REQUIRES_REVIEW"}
                blocked.add(key(task))
                pending_persist = True
                # Never relaunch a reproducible fault every 30 minutes.
                print("MANHUA_SLOT_FAILED_HELD_IN_PRIVATE_QUEUE",
                      {"gpu": slot, "episode": task["episode"]}, flush=True)
        if pending_persist:
            try:
                persist_dataset(results_ref, "results.json", record, create=create_record)
                create_record = False
                pending_persist = False
            except Exception as exc:
                print("MANHUA_RESULT_PERSIST_RETRY_KEEP_WORKERS",
                      type(exc).__name__, flush=True)
        eligible = [t for t in tasks if key(t) not in finished
                    and key(t) not in blocked
                    and key(t) not in attempted
                    and all(key(a["task"]) != key(t) for a in active.values())]
        for slot in (0, 1):
            if slot not in active and eligible:
                task = eligible.pop(0)
                attempted.add(key(task))
                try:
                    active[slot] = start_worker(task, slot, owner)
                except Exception as exc:
                    record["blocked"][key(task)] = {"gpu": slot,
                        "reason": type(exc).__name__, "state": "FAILED_REQUIRES_REVIEW"}
                    blocked.add(key(task))
                    pending_persist = True
                    print("MANHUA_SLOT_INPUT_FAILED_OTHER_GPU_CONTINUES",
                          {"gpu": slot, "error_type": type(exc).__name__}, flush=True)
        if eligible:
            print("MANHUA_PRIVATE_QUEUE_WAITING", {"count": len(eligible)}, flush=True)
        quiet = quiet + 1 if not active and not eligible and not pending_persist else 0
        if quiet >= idle_polls:
            print("MANHUA_SUPERVISOR_IDLE_EXIT", {"completed": len(finished),
                  "held": len(blocked)}, flush=True)
            return {"completed": len(finished), "held": len(blocked),
                    "unfinished": len(attempted - finished - blocked)}
        time.sleep(max(10, poll_seconds))


def cli() -> None:
    parser = argparse.ArgumentParser(description="Private dual-T4 manhua dispatch")
    sub = parser.add_subparsers(dest="command", required=True)
    send = sub.add_parser("enqueue")
    send.add_argument("--queue-ref", required=True)
    send.add_argument("--story-id", required=True)
    send.add_argument("--episode", type=int, required=True)
    send.add_argument("--private-dataset", required=True)
    send.add_argument("--source-sha256", default="")
    send.add_argument("--progress-dataset", default="")
    send.add_argument("--phase", choices=VALID_PHASES, default="assets")
    send.add_argument("--quality", choices=VALID_QUALITIES, default="quality")
    work = sub.add_parser("supervise")
    work.add_argument("--queue-ref", required=True)
    work.add_argument("--results-ref", required=True)
    work.add_argument("--owner", required=True)
    args = parser.parse_args()
    if args.command == "enqueue":
        add_approved_task(args.queue_ref, {"story_id": args.story_id,
            "episode": args.episode, "private_dataset": args.private_dataset,
            "source_sha256": args.source_sha256,
            "progress_dataset": args.progress_dataset,
            "phase": args.phase, "quality": args.quality, "voice_profile": VOICE})
    else:
        supervise(args.queue_ref, args.results_ref, args.owner)


if __name__ == "__main__":
    cli()
