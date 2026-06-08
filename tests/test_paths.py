import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pinyin_tones import paths


class TestRuntimePaths(unittest.TestCase):
    def test_get_app_root_uses_executable_dir_when_frozen(self):
        executable = "C:/Apps/Pinyin/pinyin_tones.exe"
        with mock.patch.object(paths.sys, "frozen", True, create=True), \
             mock.patch.object(paths.sys, "executable", executable):
            self.assertEqual(paths.get_app_root(), str(Path(executable).parent))

    def test_get_state_dir_prefers_writable_app_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(paths.get_state_dir(temp_dir), temp_dir)

    def test_get_state_dir_falls_back_to_user_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fallback = Path(temp_dir) / "state"

            with mock.patch.object(paths, "is_writable_dir", return_value=False), \
                 mock.patch.object(paths, "get_user_data_dir", return_value=str(fallback)):
                self.assertEqual(paths.get_state_dir("C:/read-only"), str(fallback))

            self.assertTrue(fallback.exists())


if __name__ == "__main__":
    unittest.main()
