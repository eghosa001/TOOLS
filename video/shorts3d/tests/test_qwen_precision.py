#!/usr/bin/env python3
"""Regression tests for the Qwen CUDA NaN issue found on Kaggle Tesla T4."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qwen_audio import choose_backend


class FakeCuda:
    def __init__(self, available: bool, major: int = 7):
        self.available_value = available
        self.major = major

    def is_available(self):
        return self.available_value

    def get_device_capability(self, index: int):
        assert index == 0
        return self.major, 5


class FakeTorch:
    float32 = "float32"
    bfloat16 = "bfloat16"
    float16 = "float16"

    def __init__(self, available: bool, major: int = 7):
        self.cuda = FakeCuda(available, major)
        self.float_precision = None

    def set_float32_matmul_precision(self, mode):
        self.float_precision = mode


class QwenDtypeTest(unittest.TestCase):
    def test_tesla_t4_never_uses_fp16(self):
        t = FakeTorch(True, major=7)
        self.assertEqual(choose_backend(t), ("cuda:0", "float32"))
        self.assertEqual(t.float_precision, "highest")

    def test_ampere_uses_native_bfloat16(self):
        t = FakeTorch(True, major=8)
        self.assertEqual(choose_backend(t), ("cuda:0", "bfloat16"))

    def test_cpu_is_float32(self):
        t = FakeTorch(False)
        self.assertEqual(choose_backend(t), ("cpu", "float32"))

    def test_cpu_override_on_t4(self):
        t = FakeTorch(True, major=7)
        self.assertEqual(choose_backend(t, force_cpu=True), ("cpu", "float32"))


if __name__ == "__main__":
    unittest.main()
