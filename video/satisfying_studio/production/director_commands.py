"""Strict allowlist for decisions made by an ASMR vision reviewer/agent.

Only physically safe, non-destructive post-bake appearance changes may be
applied automatically. Never execute arbitrary Python from model text.
"""
from __future__ import annotations
import math

LIMITS = {
    "camera_lens_mm": (40.0, 95.0, .22),
    "gel_roughness": (.04, .35, .5),
    "gel_transmission": (.18, .85, .50),
    "gel_subsurface": (.05, .60, .50),
    "key_light_energy": (40.0, 400.0, .45),
}
class DirectorCommandError(ValueError):
    pass


def validate_directive(data, present):
    if not isinstance(data, dict):
        raise DirectorCommandError("Director directives must be JSON object")
    if set(data) != {"source_blend_sha256", "reason", "changes"}:
        raise DirectorCommandError("Unexpected director command fields")
    sha = data["source_blend_sha256"]
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise DirectorCommandError("Missing exact source .blend SHA256")
    reason = data["reason"]
    if not isinstance(reason, str) or not 20 <= len(reason) <= 400:
        raise DirectorCommandError("Need specific visual defect and frame-number rationale")
    changes = data["changes"]
    if not isinstance(changes, dict) or not 1 <= len(changes) <= 4:
        raise DirectorCommandError("1-4 precise creative changes required")
    for name, target in changes.items():
        if name not in LIMITS:
            raise DirectorCommandError("Unapproved or physics-mutating Blender command: " + name)
        if not isinstance(target, (int, float)) or not math.isfinite(target):
            raise DirectorCommandError("Non-finite/invalid target " + name)
        low, high, max_fraction = LIMITS[name]
        if not low <= target <= high:
            raise DirectorCommandError("Out-of-bounds Blender parameter: " + name)
        if name not in present:
            raise DirectorCommandError("Missing baseline Blender value: " + name)
        baseline = present[name]
        if not isinstance(baseline, (int, float)) or not math.isfinite(baseline):
            raise DirectorCommandError("Invalid baseline Blender value: " + name)
        if baseline != 0 and abs(target - baseline) / abs(baseline) > max_fraction:
            raise DirectorCommandError("Unsafe large change of " + name)
    return {name: float(target) for name, target in changes.items()}
