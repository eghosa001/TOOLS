"""Detect apparent glass-on-ceramic first impact timing from real Blender Bullet positions.

These timestamps guide manual recording placement; the final film still needs
per-contact watch-and-listen review to confirm one-frame synchronization.
"""
from __future__ import annotations
import math

RELEASES=(18,29,40,51,62,73,84)

def first_impact_events(frames):
    if not isinstance(frames,list) or len(frames)!=120:
        raise ValueError("Missing 120 consecutive original physics frames")
    for idx,row in enumerate(frames,1):
        if row.get("frame")!=idx or len(row.get("marble_centers_xyz",[]))!=7:
            raise ValueError("Incomplete or reordered Bullet physics evidence")
        for centre in row["marble_centers_xyz"]:
            if len(centre)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in centre):
                raise ValueError("Invalid physical marble coordinates")
    events=[]
    for bead,release in enumerate(RELEASES):
        # With an actual ceramic bowl, first sphere-bowl strike occurs near
        # center z≈0.3-0.4m. Detect first crossing of collision neighbourhood
        # after release, rather than estimating a timestamp from release alone.
        seen=None
        for i in range(release+1,120):
            current=frames[i]["marble_centers_xyz"][bead]
            previous=frames[i-1]["marble_centers_xyz"][bead]
            if current[2] <= .42 and previous[2] > .42:
                velocity=24*(previous[2]-current[2])
                seen={"marble_index":bead,"source_release_frame":release,
                      "impact_frame":i+1,"impact_position_xyz":[round(float(x),5) for x in current],
                      "approx_inbound_velocity_m_s":round(max(0.,velocity),3),
                      "onset_method":"first physical bowl-height crossing",
                      "precision":"requires actual one-frame sync visual+headphone review"}
                break
        if seen is None:
            raise ValueError("One of seven original glass beads never reaches the bowl")
        events.append(seen)
    if len({e["impact_frame"] for e in events})<5:
        raise ValueError("Impact sequence lacks distinct audible events")
    return events
