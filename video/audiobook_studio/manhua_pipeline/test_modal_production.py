"""Offline, secret-free safeguards for replacing Kaggle with private Modal."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "video/audiobook_studio/manhua_pipeline/modal_production.py"
TRANSFER = ROOT / "video/audiobook_studio/manhua_pipeline/modal_private_source_transfer.py"
WORKFLOW = ROOT / ".github/workflows/manhua-audiobook-private.yml"
LEGACY = ROOT / ".github/workflows/manhua-dual-t4-auto-dispatch.yml"

def pure_cost_guard():
    """Test the actual cost-check code without Modal installation or any GPU calls."""
    tree = ast.parse(MODULE.read_text())
    nodes = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("RATES",) for t in stmt.targets):
            nodes.append(stmt)
        if isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Tuple) and any(
                    isinstance(v, ast.Name) and v.id in ("TTS_SECONDS", "ART_SECONDS")
                    for v in t.elts) for t in stmt.targets):
            nodes.append(stmt)
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "budget_guard":
            nodes.append(stmt)
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    scope = {}
    exec(compile(module, str(MODULE), "exec"), scope)
    return scope["budget_guard"]

class ModalAudiobookSafetyTests(unittest.TestCase):
    def test_all_python_sources_compile(self):
        for p in (MODULE, TRANSFER):
            compile(p.read_text(), str(p), "exec")

    def test_l4_l4_budget_is_cheapest_safe_default(self):
        got = pure_cost_guard()()
        self.assertEqual((got["voice_gpu"], got["art_gpu"]), ("L4", "L4"))
        self.assertLess(got["max_gpu_envelope_usd"], 0.80)
        self.assertIs(got["cpu_and_ram_included"], False)

    def test_h100_is_blocked_by_default_budget(self):
        with self.assertRaises(ValueError):
            pure_cost_guard()(tts_gpu="H100", art_gpu="H100")

    def test_unknown_gpus_and_nonsense_budgets_are_rejected(self):
        guard = pure_cost_guard()
        for params in ({"tts_gpu":"A999"}, {"maximum_usd":0},
                       {"maximum_usd":300}, {"art_gpu":"INVALID"}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                guard(**params)

    def test_authorized_ryan_voice_is_not_replaced(self):
        src = MODULE.read_text()
        self.assertIn("voice_profile", src)
        self.assertIn("engine.voice_chunks(parts, dest", src)
        self.assertNotIn("edge_tts", src)
        self.assertNotIn("gTTS", src)
        self.assertIn("image_model_rights_reviewed", src)

    def test_private_hash_bound_assets_and_human_gate(self):
        src = MODULE.read_text()
        for term in ("open_package", "source_sha256", "PRIVATE_SCENE_TIMELINE.json",
                     "require_visual_qa=True", "release_approved", "ready_for_youtube",
                     "human_listening_approved", "with_mount_options(read_only=True)"):
            with self.subTest(term=term):
                self.assertIn(term, src)
        self.assertNotIn("youtube.upload", src)

    def test_separate_gpu_tasks_and_cpu_assembly(self):
        src = MODULE.read_text()
        self.assertIn("modal.FunctionCall.gather(tts, art)", src)
        self.assertIn("generate_ryan.with_options(gpu=tts_gpu).spawn", src)
        self.assertIn("generate_art.with_options(gpu=art_gpu).spawn", src)
        self.assertIn("def assemble_private_review(", src)
        self.assertIn('gpu_image =', src)
        self.assertIn('cpu_image =', src)

    def test_default_workflow_is_modal_and_no_legacy_gpu_submit(self):
        wf = WORKFLOW.read_text()
        self.assertIn("modal run -m video.audiobook_studio.manhua_pipeline.modal_production", wf)
        self.assertNotIn("kaggle kernels push", wf)
        self.assertIn("MODAL_TOKEN_ID", wf)
        self.assertIn("MODAL_TOKEN_SECRET", wf)
        self.assertIn("drive_source_file_id", wf)
        self.assertIn("PRIVATE", wf)

    def test_legacy_auto_dispatch_disabled_not_deleted(self):
        legacy = LEGACY.read_text()
        self.assertIn("workflow_dispatch:", legacy)
        self.assertNotIn(re.search(r"^  schedule:", legacy, re.M).group(0)
                         if re.search(r"^  schedule:", legacy, re.M) else "NO_SCHEDULE", "NO_SCHEDULE")
        self.assertIsNone(re.search(r"^  schedule:", legacy, re.M))
        self.assertIsNone(re.search(r"^  push:", legacy, re.M))

if __name__ == "__main__":
    unittest.main()
