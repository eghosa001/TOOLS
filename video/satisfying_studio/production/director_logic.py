"""Free, deterministic decisions for the Blender ASMR Production Director.

Pure Python: no external network, GPU or paid inference. Only correct defects
with measurable evidence; a vision model or human must judge aesthetics.
"""
from __future__ import annotations
import math


class DirectorBlocked(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DirectorBlocked(message)


def _numbers(extents):
    require(len(extents) >= 3, "Camera decision requires multiple actual physical frames")
    values = []
    for item in extents:
        for axis in ("x", "y"):
            lo, hi = item["min_" + axis], item["max_" + axis]
            require(isinstance(lo, (float, int)) and math.isfinite(lo)
                    and isinstance(hi, (float, int)) and math.isfinite(hi)
                    and lo <= hi, "Invalid physical camera coordinates")
            values.extend((float(lo), float(hi)))
    return values


def framing_action(extents, lens, margin=0.055, max_zoom_out=0.18):
    """Return a cheap, safe camera fix without rebaking physics.

    Only bounded zoom-out may be made autonomously. Extreme cropping is a
    creative/composition failure and must be directed, never blindly hidden.
    """
    values = _numbers(extents)
    require(0 < margin < .25 and 0 < max_zoom_out < .5, "Bad camera safety settings")
    require(isinstance(lens, (float, int)) and math.isfinite(lens) and lens > 0,
            "Invalid active lens")
    defect = any(v < margin or v > 1 - margin for v in values)
    if not defect:
        return {"action": "keep", "lens": round(float(lens), 5),
                "zoom_factor": 1.0, "frame_count": len(extents)}
    # With a fixed camera position and shift, perspective projection of the
    # same 3D point scales linearly around the central normalized film coords.
    farthest = max(abs(v - .5) for v in values)
    require(farthest > .0, "Degenerate camera extent")
    factor = min(1.0, (.5 - margin) / farthest) * .996
    require(factor >= 1.0 - max_zoom_out,
            "Unsafe to auto-zoom %.1f%%: re-stage action/camera instead of shrinking subject"
            % ((1-factor)*100))
    corrected = round(float(lens)*factor, 5)
    require(corrected > 0, "Computed focal length invalid")
    return {"action": "zoom_out", "lens": corrected,
            "zoom_factor": factor, "frame_count": len(extents)}


def validate_framing(extents, margin=0.045):
    _numbers(extents)
    invalid = [x for x in extents if x["min_x"] < margin or
               x["max_x"] > 1 - margin or x["min_y"] < margin or
               x["max_y"] > 1 - margin]
    require(not invalid, "ASMR director: material outside composition: %s" % invalid)
    return True


def float_diagnostic(bounds, tolerance=.06, end_frame=120):
    """Measured geometry hint; no invented photorealism quality score.

    Physically plausible resting minimum z is measured from the very first
    baked frame. Bounding-box minimum on a sampled frame is conservative.
    """
    require(len(bounds) >= 2, "Need physical initial and release frames")
    items = {v["frame"]: v for v in bounds}
    require(1 in items and end_frame in items, "Missing rest/release physics evidence")
    bottom_start = items[1]["min_xyz"][2]
    bottom_end = items[end_frame]["min_xyz"][2]
    require(all(math.isfinite(v) for v in (bottom_start, bottom_end)),
            "Invalid physics contact bounds")
    return {"start_min_z": bottom_start, "end_min_z": bottom_end,
            "upward_displacement": round(bottom_end - bottom_start, 5),
            "floating_risk": bottom_end - bottom_start > tolerance}


def material_parameter_warnings(transmission, subsurface, roughness):
    """Bound extreme CG presets; never claim appearance can be scored from nodes."""
    items = (transmission, subsurface, roughness)
    require(all(isinstance(x, (int, float)) and math.isfinite(x) for x in items),
            "Invalid shader parameters")
    require(all(0 <= x <= 1 for x in items), "Shader values outside physical range")
    alerts = []
    if transmission > .85 and subsurface < .06:
        alerts.append("glass-like shader risk: transmission too dominant for wet gel")
    if roughness < .015:
        alerts.append("mirror-perfect surface risk: lacks believable micro-roughness")
    if subsurface > .7 and transmission < .2:
        alerts.append("opaque wax-like gel risk: strong scattering")
    return alerts
