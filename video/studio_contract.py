"""Shared Blender scene/story input contract. No AI model or paid dependency."""
from __future__ import annotations
import re

# Presets remain useful as fallbacks. Hex/RGB supplies millions of other colours.
COLORS = {
    "blue": "#1c61d9", "coral": "#e64048", "green": "#238c5c",
    "purple": "#6942bf", "gold": "#d8a32e", "turquoise": "#18aabb",
    "ochre": "#b86d21", "red": "#ff0000", "orange": "#ff8c00",
    "yellow": "#ffff00", "pink": "#ffc0cb", "white": "#ffffff",
    "black": "#000000", "brown": "#a52a2a", "grey": "#808080",
    "gray": "#808080", "cyan": "#00ffff", "magenta": "#ff00ff",
    "violet": "#8f00ff", "lavender": "#e6e6fa", "navy": "#000080",
    "beige": "#f5f5dc", "teal": "#008080", "maroon": "#800000",
    "silver": "#c0c0c0", "lime": "#00ff00", "peach": "#ffdab9",
    "plum": "#dda0dd", "salmon": "#fa8072", "indigo": "#4b0082",
}
STAGES = {
    "auto", "living_room", "forest", "village", "city", "beach",
    "desert", "classroom", "office", "palace", "custom", "sunpatch_court",
}
CAMERAS = {"automatic", "wide", "close", "medium"}
_HEX = re.compile(r"^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB = re.compile(r"^rgba?\(([^)]*)\)$", re.I)

def rgba(value):
    """Return Blender RGBA floats. RGB channel values: 0..1 or 0..255."""
    if isinstance(value, str):
        text = value.strip().lower()
        text = COLORS.get(text, text)
        match = _HEX.fullmatch(text)
        if match:
            digits = match.group(1)
            if len(digits) in (3, 4):
                digits = "".join(ch * 2 for ch in digits)
            if len(digits) == 6:
                digits += "ff"
            return tuple(int(digits[i:i+2], 16) / 255 for i in range(0, 8, 2))
        match = _RGB.fullmatch(text)
        if not match:
            raise ValueError("Use a colour name, #RRGGBB, rgb(...), or RGB array")
        channels = [x.strip() for x in match.group(1).split(",")]
        if len(channels) not in (3, 4):
            raise ValueError("RGB colour must have three channels, optionally alpha")
        try:
            rgb_values = [float(ch) for ch in channels[:3]]
            alpha = float(channels[3]) if len(channels) == 4 else 1.0
        except ValueError as exc:
            raise ValueError("RGB colour contains non-numeric values") from exc
        if any(not 0 <= v <= 255 for v in rgb_values) or not 0 <= alpha <= 1:
            raise ValueError("CSS RGB values must be 0..255; alpha 0..1")
        return (*(v / 255 for v in rgb_values), alpha)
    if isinstance(value, dict):
        if not all(key in value for key in ("r", "g", "b")):
            raise ValueError("Colour object requires r, g, b")
        value = [value["r"], value["g"], value["b"], value.get("a", 1.0)]
    if isinstance(value, (list, tuple)) and len(value) in (3, 4):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value):
            raise ValueError("RGB channels must be numeric")
        rgb = list(value[:3])
        alpha = value[3] if len(value) == 4 else 1.0
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")
        if all(0 <= v <= 1 for v in rgb):
            return (float(rgb[0]), float(rgb[1]), float(rgb[2]), float(alpha))
        if all(0 <= v <= 255 for v in rgb):
            return (*(float(v) / 255 for v in rgb), float(alpha))
    raise ValueError("Use a named colour, hex, rgb(...), or valid RGB array/object")

def validate_scene_contract(story):
    """Validate ordered, inclusive 1-based line ranges without changing dialogue."""
    scenes = story.get("scenes")
    if scenes is None:
        return []
    if not isinstance(scenes, list) or not scenes or len(scenes) > 64:
        raise ValueError("scenes must be a nonempty list with at most 64 entries")
    length = len(story.get("dialogue", []))
    next_line = 1
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be an object")
        start, end = scene.get("start_line"), scene.get("end_line")
        if type(start) is not int or type(end) is not int or start != next_line or not start <= end <= length:
            raise ValueError(f"Scene {index} must cover dialogue line {next_line} onward, with valid inclusive start_line/end_line")
        stage = scene.get("stage", "auto")
        if stage not in STAGES:
            raise ValueError(f"Scene {index} has unknown stage: {stage}")
        if scene.get("camera", "automatic") not in CAMERAS:
            raise ValueError(f"Scene {index} camera must be automatic, wide, medium or close")
        if "visual_prompt" in scene and not isinstance(scene["visual_prompt"], str):
            raise ValueError(f"Scene {index} visual_prompt must be a string")
        if "background_color" in scene:
            rgba(scene["background_color"])
        if stage == "custom":
            filepath = scene.get("environment_file")
            if not isinstance(filepath, str) or not filepath.lower().endswith((".glb", ".gltf")):
                raise ValueError(f"Scene {index} custom stage needs environment_file (.glb/.gltf)")
        next_line = end + 1
    if next_line != length + 1:
        raise ValueError(f"Scenes do not cover the final dialogue lines {next_line}..{length}")
    return scenes
