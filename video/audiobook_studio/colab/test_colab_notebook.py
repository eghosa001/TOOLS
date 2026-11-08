"""Offline regression tests: avoid the Colab PEFT failure and double sign-in."""
import json
from pathlib import Path
import unittest

NOTEBOOK = Path(__file__).with_name("Eternal_Dao_Episode01_Bulk_Illustrations.ipynb")


class ColabIllustrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cls.cells = ["".join(c["source"]) for c in cls.notebook["cells"]]

    def test_valid_notebook_and_python_cells(self):
        self.assertEqual(self.notebook["nbformat"], 4)
        self.assertEqual(self.notebook["metadata"]["accelerator"], "GPU")
        for i, cell in enumerate(self.cells[2:], start=2):
            compile(cell, f"notebook-cell-{i}", "exec")
        self.assertTrue(all(not c.get("outputs") for c in self.notebook["cells"]
                            if c["cell_type"] == "code"))

    def test_compatible_peft_installed_and_checked_before_model(self):
        self.assertIn('"peft==0.17.1"', self.cells[1])
        self.assertIn('"diffusers==0.35.2"', self.cells[1])
        self.assertIn("from peft import LoraConfig", self.cells[2])
        self.assertIn("load_lora_weights", self.cells[2])
        self.assertLess(self.cells[2].index("from peft import LoraConfig"),
                        self.cells[2].index("drive.mount"))
        self.assertNotIn("hf_hub_download", self.cells[2])

    def test_single_google_drive_authorization_and_private_sources(self):
        self.assertIn('drive.mount(str(MOUNT))', self.cells[2])
        self.assertNotIn("auth.authenticate_user", "".join(self.cells[1:]))
        self.assertNotIn("docs.documents().get", "".join(self.cells[1:]))
        self.assertIn("EP01_D03_APPROVED_SCRIPT.txt", self.cells[2])
        self.assertIn("EP01_D03_APPROVED_STORYBOARD.txt", self.cells[2])
        self.assertIn("D03-612d3c8d39d1", self.cells[3])

    def test_resume_and_failure_reporting(self):
        generator = self.cells[4]
        for required in ("valid_image", "RETRIES_PER_IMAGE", "IMAGE",
                         "PRIVATE_EP01_ERROR_LOG.jsonl",
                         "PRIVATE_EP01_PROGRESS.json", "PRIVATE_EP01_STATUS.json",
                         "PRIVATE_EP01_DONE.json", "PRIVATE_EP01_ILLUSTRATION_MANIFEST.json",
                         'temp.replace(dest)', "owner_artwork_approval",
                         'compilation_allowed":False'):
            self.assertIn(required, generator)
        self.assertIn("if valid_image(dest):\n            continue", generator)
        self.assertIn("already stored", generator.lower())

    def test_no_image_display_or_public_story(self):
        code = "".join(self.cells[1:])
        self.assertNotIn("display(", code)
        self.assertNotIn("plt.imshow(", code)
        self.assertNotIn("kaggle", code.lower())
        self.assertNotIn("CHAPTER TWO\nThe Weight", code)
        self.assertIn("compilation_allowed", self.cells[4])


if __name__ == "__main__":
    unittest.main()
