#!/usr/bin/env python3
"""Patch the legacy embedded CartoonStudio renderer for 2–4 speaking characters.

Used only when preparing the notebook in memory for an explicitly requested
render. The original source archive remains embedded in the repository notebook.
"""
from __future__ import annotations

import base64
import hashlib
import io
import re
from pathlib import Path
import zipfile

ARCHIVE_RE = re.compile(r"(SOURCE_ARCHIVE_B64\s*=\s*)(['\"])([A-Za-z0-9+/=]+)\2")


def replace_exact(text: str, old: str, new: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"CartoonStudio source layout changed: expected {expected} copy/copies of {old[:85]!r}, found {count}")
    return text.replace(old, new)


def patch_source(filename: str, text: str) -> str:
    """Upgrade the embedded engine instead of constraining Blender inputs."""
    if filename.endswith("/cartoon_studio/story.py"):
        text = replace_exact(
            text, "from pathlib import Path",
            "from pathlib import Path\nfrom .studio_contract import rgba, validate_scene_contract",
        )
        text = replace_exact(
            text, "if not isinstance(chars, dict) or len(chars) != 2:",
            "if not isinstance(chars, dict) or not chars:",
        )
        text = replace_exact(
            text, "raise ValueError('MVP requires exactly two named characters')",
            "raise ValueError('Specify at least one named character')",
        )
        text = replace_exact(
            text,
            "if 'visual_prompt' in data and (not isinstance(data['visual_prompt'], str) or len(data['visual_prompt']) > 1000):",
            "if 'visual_prompt' in data and not isinstance(data['visual_prompt'], str):",
        )
        text = replace_exact(
            text,
            "raise ValueError('visual_prompt must be a string of at most 1000 characters')",
            "raise ValueError('visual_prompt must be a string')",
        )
        text = replace_exact(
            text,
            "if spec.get('color', 'blue') not in COLORS:\n            raise ValueError(f'Unsupported character color for {name}')",
            "try:\n            rgba(spec.get('color', 'blue'))\n        except ValueError as error:\n            raise ValueError(f'Invalid color for {name}: {error}') from error",
        )
        text = replace_exact(text, "    return data\n", "    validate_scene_contract(data)\n    return data\n")
        text = replace_exact(
            text,
            "ACTIONS = {'none', 'wave', 'nod', 'point'}",
            "ACTIONS = {'none', 'wave', 'nod', 'point', 'walk', 'turn', 'hop', 'clap'}",
        )
        text = replace_exact(
            text,
            "SCENES = {'auto', 'living_room', 'forest', 'village', 'city', 'beach', 'desert', 'classroom', 'office', 'palace'}",
            "SCENES = {'auto', 'living_room', 'forest', 'village', 'city', 'beach', 'desert', 'classroom', 'office', 'palace', 'custom'}",
        )
    elif filename.endswith("/cartoon_studio/cli.py"):
        text = replace_exact(
            text, "    story = read_story(args.story)\n",
            "    story = read_story(args.story)\n    if story.get('scenes'):\n        from .studio_scenes import render_scene_sequence\n        return render_scene_sequence(story, args, generate)\n",
        )
        text = replace_exact(
            text, "            'CARTOON_QUALITY': args.quality,",
            "            'CARTOON_QUALITY': args.quality,\n            'CARTOON_SCENE_OPTIONS': json.dumps(story.get('scene_options', {})),",
        )
    elif filename.endswith("/renderer/blender_scene.py"):
        text = replace_exact(
            text,
            "    # Ambient blinking independent of current speaker.",
            """        elif event.get('action') == 'point':
            arm = actor['arms'][1]
            for t, theta in ((0,0),(.25,-1.10),(.75,-1.10),(1,0)):
                frame = max(1, min(FRAMES, round(start_frame+t*(end_frame-start_frame))))
                arm.rotation_euler[1] = theta
                arm.keyframe_insert(data_path='rotation_euler', frame=frame)
        elif event.get('action') == 'walk':
            root = actor['root']
            base_x, base_y, base_z = tuple(root.location)
            for t, dx, dz in ((0,0,0),(.25,.11,.05),(.5,.22,0),(.75,.33,.05),(1,0,0)):
                frame = max(1, min(FRAMES, round(start_frame+t*(end_frame-start_frame))))
                root.location = (base_x+dx,base_y,base_z+dz)
                root.keyframe_insert(data_path='location', frame=frame)
        elif event.get('action') == 'hop':
            root = actor['root']
            base_z = root.location.z
            for t, dz in ((0,0),(.3,.17),(.6,.21),(1,0)):
                frame = max(1, min(FRAMES, round(start_frame+t*(end_frame-start_frame))))
                root.location.z = base_z+dz
                root.keyframe_insert(data_path='location', frame=frame)
        elif event.get('action') == 'turn':
            root = actor['root']
            base_yaw = root.rotation_euler[2]
            for t, angle in ((0,0),(.4,.3),(.65,.3),(1,0)):
                frame = max(1, min(FRAMES, round(start_frame+t*(end_frame-start_frame))))
                root.rotation_euler[2] = base_yaw+angle
                root.keyframe_insert(data_path='rotation_euler', frame=frame)
        elif event.get('action') == 'clap':
            for t, angle in ((0,0),(.2,.65),(.4,0),(.65,.65),(1,0)):
                frame = max(1, min(FRAMES, round(start_frame+t*(end_frame-start_frame))))
                for arm in actor['arms']:
                    arm.rotation_euler[1] = angle
                    arm.keyframe_insert(data_path='rotation_euler', frame=frame)
    # Ambient blinking independent of current speaker.""",
        )
        text = replace_exact(
            text, "camera.location = (0, -7.2, 2.55)",
            "camera.location = (0, -max(7.2, len(names)*1.75 + 2.0), 2.55)",
            expected=2,
        )
        text = replace_exact(
            text,
            "    color = MAT[color_name]",
            "    import sys as _sys\n    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n    from cartoon_studio.studio_contract import rgba\n    color = material(name + ' body color', rgba(color_name))",
        )
        text = replace_exact(
            text, "    # Deliberate hard cuts are safer than interpolating a camera through scene geometry.",
            "    options = json.loads(os.environ.get('CARTOON_SCENE_OPTIONS', '{}'))\n    camera_style = options.get('camera', 'automatic')\n    # Deliberate hard cuts are safer than interpolating a camera through scene geometry.",
        )
        text = replace_exact(
            text, "        if index % 4 == 0:",
            "        if camera_style == 'wide' or (camera_style == 'automatic' and index % 4 == 0):",
        )
        text = replace_exact(
            text, "            camera.location = (speaker_x*.70, -5.0, 2.45)",
            "            camera.location = (speaker_x*.70, -3.9 if camera_style == 'close' else -5.0, 2.45)",
        )
        text = replace_exact(
            text, "    add_stage(scene_kind)",
            "    options = json.loads(os.environ.get('CARTOON_SCENE_OPTIONS', '{}'))\n    if scene_kind == 'custom':\n        environment = options.get('environment_file')\n        if not environment or not Path(environment).is_file():\n            raise FileNotFoundError('Custom stage requires an attached environment_file GLB/GLTF in Kaggle')\n        bpy.ops.import_scene.gltf(filepath=str(environment))\n    else:\n        add_stage(scene_kind)",
        )
        text = replace_exact(
            text, "    scene.world.color = world_tint[:3]",
            "    if 'background_color' in options:\n        import sys as _sys\n        _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n        from cartoon_studio.studio_contract import rgba\n        world_tint = rgba(options['background_color'])\n    scene.world.color = world_tint[:3]",
        )
    return text


def upgrade_notebook_embedded_source(notebook: dict) -> None:
    """Modify the ZIP stored in SOURCE_ARCHIVE_B64 in the notebook's first code cell.

    Leave dialogue, runtime commands and all non-affected source files unchanged.
    """
    matches = [
        cell for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
        and "SOURCE_ARCHIVE_B64 =" in "".join(cell.get("source", []))
    ]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one CartoonStudio source archive cell")
    cell = matches[0]
    body = "".join(cell["source"])
    found = ARCHIVE_RE.search(body)
    if not found:
        raise RuntimeError("Could not locate the embedded CartoonStudio source ZIP")
    original = base64.b64decode(found.group(3), validate=True)
    updated_bytes = io.BytesIO()
    changes = []
    with zipfile.ZipFile(io.BytesIO(original)) as zin:
        with zipfile.ZipFile(updated_bytes, "w") as zout:
            for entry in zin.infolist():
                data = zin.read(entry.filename)
                if entry.filename.endswith(("/cartoon_studio/story.py", "/cartoon_studio/cli.py", "/renderer/blender_scene.py")):
                    data = patch_source(entry.filename, data.decode("utf-8")).encode("utf-8")
                    changes.append(entry.filename)
                zout.writestr(entry, data)
            root = Path(__file__).resolve().parent
            for source_name, destination in (
                ("studio_contract.py", "CartoonStudio/cartoon_studio/studio_contract.py"),
                ("studio_scenes.py", "CartoonStudio/cartoon_studio/studio_scenes.py"),
            ):
                if destination in zin.namelist():
                    raise RuntimeError(f"Bundled source already contains {destination}")
                payload = (root / source_name).read_bytes()
                compile(payload.decode("utf-8"), destination, "exec")
                zout.writestr(destination, payload)
    if len(changes) != 3:
        raise RuntimeError(f"Expected three CartoonStudio core source files, found {changes}")
    old_checksum = hashlib.sha256(original).hexdigest()
    old_checksum_line = "expected_sha256 = " + repr(old_checksum)
    if body.count(old_checksum_line) != 1:
        raise RuntimeError("Original embedded source checksum does not match; refusing to modify")
    new_archive = updated_bytes.getvalue()
    encoded = base64.b64encode(new_archive).decode("ascii")
    body = body[:found.start(3)] + encoded + body[found.end(3):]
    body = body.replace(old_checksum_line,
                        "expected_sha256 = " + repr(hashlib.sha256(new_archive).hexdigest()), 1)
    cell["source"] = body.splitlines(keepends=True)
