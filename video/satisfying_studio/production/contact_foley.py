"""Physical contact aware *timing* for manually selected authentic ASMR Foley.

No sound is synthesized or artistically approved here. In particular a visual
roller that does not touch a baked gel must never be dubbed with squishes.
"""
from __future__ import annotations
import math

def measured_contact_schedule(rows):
    if not isinstance(rows,list) or len(rows)<9:
        raise ValueError("Missing at least nine measured physical contact checkpoints")
    samples={}
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Invalid contact row")
        frame=row.get("frame")
        gap=row.get("surface_gap_m")
        height=row.get("gel_surface_z")
        if type(frame) is not int or type(gap) not in (int,float) or type(height) not in (int,float):
            raise ValueError("Baked contact has missing frame/surface/gap")
        if frame in samples or not math.isfinite(gap) or not math.isfinite(height):
            raise ValueError("Duplicate frame or invalid physics geometry")
        samples[frame]=dict(frame=frame,gap=gap,height=height)
    ordered=[samples[k] for k in sorted(samples)]
    if ordered[0]["frame"] != 1 or ordered[-1]["frame"] != 120:
        raise ValueError("Physical evidence must cover the complete 120-frame shot")
    # The existence of an MP4 or a passed bake is not actual *contact*.
    if any(v["gap"] < -.025 for v in ordered):
        raise ValueError("Reject impossible collider penetration before any Foley")
    contact=[v for v in ordered if -.025 <= v["gap"] <= .013]
    if len(contact)<3:
        raise ValueError("Not enough real touch/press/release evidence for ASMR Foley")
    if ordered[-1]["gap"] <= .013:
        raise ValueError("Gel tool does not audibly release within planned shot")
    first=contact[0]["frame"]
    peak=min(contact,key=lambda x:x["gap"])["frame"]
    release=contact[-1]["frame"]
    if peak-first<12 or release-peak<8:
        raise ValueError("Press/release too short for physically expressive Foley")
    if first>96:
        raise ValueError("Contact occurs too late for a useful five-second Short")
    body_rest=samples.get(20,ordered[0])["height"]
    stressed=min(samples[f]["height"] for f in (67,80) if f in samples)
    if body_rest-stressed<.012:
        raise ValueError("Baked gel did not visibly compress under roller")
    middle=first+max(1,round((peak-first)*.58))
    return {
        "first_touch":first,
        "compression":min(peak-1,middle),
        "peak_pressure":peak,
        "release":release,
        "measured_peak_clearance_m":round(min(v["gap"] for v in contact),5),
        "measured_deformation_m":round(body_rest-stressed,5),
        "manual_headphone_review_required":True,
    }

def attenuation_only_gain(peak,ceiling_dbfs=-8.0):
    """Do not normalize quiet squishes *up* into harsh fake impacts."""
    if peak<0 or not math.isfinite(peak):
        raise ValueError("Invalid audio peak")
    ceiling=10**(ceiling_dbfs/20)
    if not 0<ceiling<=1:
        raise ValueError("Invalid safe ceiling")
    return min(1.0,ceiling/peak) if peak else 1.0
