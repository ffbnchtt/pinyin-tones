import subprocess
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_PACKAGE_DIR = ROOT_DIR / "pinyin_tones"
SRC_PACKAGE_DIR = ROOT_DIR / "src" / "pinyin_tones"


class TestDevEntrypoint(unittest.TestCase):
    def test_repo_root_package_shim_finds_src_package_modules(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import importlib.util; "
                    "import pinyin_tones; "
                    "main_spec = importlib.util.find_spec('pinyin_tones.__main__'); "
                    "live_spec = importlib.util.find_spec('pinyin_tones.pinyin_live'); "
                    "print(pinyin_tones.__file__); "
                    "print(main_spec.origin if main_spec else ''); "
                    "print(live_spec.origin if live_spec else '')"
                ),
            ],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )

        lines = result.stdout.strip().splitlines()
        self.assertEqual(lines[0], str(ROOT_PACKAGE_DIR / "__init__.py"))
        self.assertEqual(lines[1], str(ROOT_PACKAGE_DIR / "__main__.py"))
        self.assertEqual(lines[2], str(SRC_PACKAGE_DIR / "pinyin_live.py"))


if __name__ == "__main__":
    unittest.main()
