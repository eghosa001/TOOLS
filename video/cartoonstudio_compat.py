"""Small compatibility patch for the embedded CartoonStudio MVP source.

The packaged v1 source supports two characters only. Keep original two-actor
behaviour, extend to a small ensemble, and add palette entries used by this episode.
This patch is applied to a freshly unpacked copy, not the base64-encoded archive.
"""
from pathlib import Path


def patch_bundled_source(root: Path) -> None:
    root = Path(root)
    story_file = root / 'cartoon_studio' / 'story.py'
    render_file = root / 'renderer' / 'blender_scene.py'

    def replace_checked(content: str, old: str, new: str, label: str) -> str:
        matches = content.count(old)
        if matches != 1:
            raise RuntimeError(
                f'CartoonStudio compatibility patch refused {label}: expected one match, found {matches}'
            )
        return content.replace(old, new, 1)

    story = story_file.read_text(encoding='utf-8')
    story = replace_checked(
        story,
        "COLORS = {'blue', 'coral', 'green', 'purple', 'gold'}",
        "COLORS = {'blue', 'coral', 'green', 'purple', 'gold', 'turquoise', 'ochre'}",
        'character palette',
    )
    story = replace_checked(
        story,
        "not isinstance(chars, dict) or len(chars) != 2",
        "not isinstance(chars, dict) or not 2 <= len(chars) <= 4",
        'character count',
    )
    story = replace_checked(
        story,
        "raise ValueError('MVP requires exactly two named characters')",
        "raise ValueError('CartoonStudio requires 2 to 4 named characters')",
        'character validation message',
    )

    render = render_file.read_text(encoding='utf-8')
    render = replace_checked(
        render,
        'PALETTE = {',
        """PALETTE = {
    'turquoise': (0.09, 0.67, 0.68, 1),
    'ochre': (0.70, 0.43, 0.16, 1),""",
        'procedural character colors',
    )
    render = replace_checked(
        render,
        "    names = list(TIMELINE['characters'].keys())\n    actors = {}",
        """    names = list(TIMELINE['characters'].keys())
    spacing = 2.30 if len(names) == 2 else 1.45
    position_by_name = {
        name: (i - (len(names) - 1) / 2) * spacing
        for i, name in enumerate(names)
    }
    actors = {}""",
        'three-actor stage placement',
    )
    position = '-1.15 if i == 0 else 1.15'
    if render.count(position) != 2:
        raise RuntimeError('CartoonStudio patch refused actor positions: expected exactly two calls')
    render = render.replace(position, 'position_by_name[name]')
    render = replace_checked(
        render,
        "speaker_x = -1.15 if event['speaker'] == names[0] else 1.15",
        """speaker_x = (names.index(event['speaker']) - (len(names) - 1) / 2) * (
                2.30 if len(names) == 2 else 1.45)""",
        'three-actor camera framing',
    )
    compile(story, str(story_file), 'exec')
    compile(render, str(render_file), 'exec')
    story_file.write_text(story, encoding='utf-8')
    render_file.write_text(render, encoding='utf-8')
    print('CartoonStudio compatibility: 2-4 actors, turquoise/ochre palette, distinct positions', flush=True)
