import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pinyin_tones import config_store


class TestConfigStore(unittest.TestCase):
    def test_load_config_returns_defaults_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.json"

            self.assertEqual(
                config_store.load_config(str(path), {"hotkey": "default"}),
                {"hotkey": "default"},
            )

    def test_save_config_writes_json_atomically(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nested" / "config.json"

            config_store.save_config(str(path), {"hotkey": "<ctrl>+p"})

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"hotkey": "<ctrl>+p"},
            )
            self.assertEqual(list(path.parent.glob(".config-*.tmp")), [])

    def test_save_config_preserves_existing_file_when_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text('{"hotkey":"old"}', encoding="utf-8")

            with mock.patch.object(config_store.os, "replace", side_effect=OSError("locked")):
                config_store.save_config(str(path), {"hotkey": "new"})

            self.assertEqual(path.read_text(encoding="utf-8"), '{"hotkey":"old"}')
            self.assertEqual(list(path.parent.glob(".config-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()

