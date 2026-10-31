"""No Kaggle token, art archive or network required."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE=Path(__file__).resolve().parents[1]/'ops'/'launch_kaggle_e101_v11.py'
spec=importlib.util.spec_from_file_location('ninefold_private_stage',MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PrivateKaggleStageTests(unittest.TestCase):
    def test_notebook_code_compiles_and_is_guarded(self):
        self.assertGreaterEqual(mod.validate_notebook(),6)
        raw=mod.NOTEBOOK.read_text(encoding='utf-8')
        self.assertNotIn('BASE64_SOURCE_ZIP',raw)
        self.assertLess(len(raw),100_000)

    def test_exact_dataset_only(self):
        rows=[{'ref':'user/asmr-master'},{'ref':'user/ninefold-s1-private-art-v11'}]
        self.assertEqual(mod.matching_private_dataset(rows,'user'),'user/ninefold-s1-private-art-v11')
        self.assertIsNone(mod.matching_private_dataset(rows,'someoneelse'))
        self.assertIsNone(mod.matching_private_dataset([{'ref':'user/ninefold-s1-private-art-v10'}],'user'))

    def test_multiple_datasets_fail_closed(self):
        with self.assertRaises(RuntimeError):
            mod.matching_private_dataset([{'ref':'x/ninefold-s1-private-art-v11'},
                {'ref':'x/ninefold-s1-private-kaggle-kit-v11'}],'x')

    def test_no_token_never_submits(self):
        with patch.dict('os.environ',{'KAGGLE_API_TOKEN':'','KAGGLE_KEY':''}):
            with patch.object(mod,'command',side_effect=AssertionError('Not allowed to call Kaggle')):
                self.assertEqual(mod.main(),2)

    def test_owner_derived_only_from_account_or_config(self):
        with patch.dict('os.environ',{'KAGGLE_USERNAME':'correct-owner'}):
            self.assertEqual(mod.owner_from_kernels([]),'correct-owner')
            self.assertEqual(mod.owner_from_kernels([{'ref':'own/k1'}]),'own')
            with self.assertRaises(RuntimeError):
                mod.owner_from_kernels([{'ref':'a/k1'},{'ref':'b/k2'}])

    def test_no_existing_notebook_is_overwritten(self):
        with patch.dict('os.environ',{'KAGGLE_API_TOKEN':'fake','KAGGLE_KEY':'','KAGGLE_USERNAME':'own'}):
            with patch.object(mod,'command',return_value='ref,title\nown/'+mod.SLUG+',Existing\n') as mocked:
                self.assertEqual(mod.main(),0)
                self.assertEqual(mocked.call_count,1)

if __name__=='__main__':unittest.main()