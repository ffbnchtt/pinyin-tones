import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from pinyin_tones import update_check
from pinyin_tones.version import is_newer_version, normalize_version, parse_version


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.offset = 0

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = len(self.payload) - self.offset
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FailingResponse:
    def read(self, size: int = -1) -> bytes:
        raise OSError("download interrupted")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestVersionHelpers(unittest.TestCase):
    def test_parse_version_accepts_optional_v_prefix(self):
        self.assertEqual(parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(parse_version("v0.2.1"), (0, 2, 1))

    def test_normalize_version_handles_invalid_values(self):
        self.assertEqual(normalize_version("v1.2.3"), "1.2.3")
        self.assertEqual(normalize_version("latest"), "latest")
        self.assertEqual(normalize_version(""), "")

    def test_is_newer_version_compares_semver(self):
        self.assertTrue(is_newer_version("0.1.1", "0.1.0"))
        self.assertTrue(is_newer_version("v0.2.0", "0.1.9"))
        self.assertFalse(is_newer_version("broken", "0.1.0"))


class TestUpdateCheckHelpers(unittest.TestCase):
    def test_select_release_asset_by_platform(self):
        assets = [
            {"name": "pinyin-tones-windows.zip", "browser_download_url": "https://example/windows"},
            {"name": "pinyin-tones-macos.zip", "browser_download_url": "https://example/macos"},
            {"name": "pinyin-tones-linux.zip", "browser_download_url": "https://example/linux"},
        ]
        self.assertEqual(
            update_check.select_release_asset(assets, "Windows"),
            ("pinyin-tones-windows.zip", "https://example/windows"),
        )
        self.assertEqual(
            update_check.select_release_asset(assets, "Darwin"),
            ("pinyin-tones-macos.zip", "https://example/macos"),
        )
        self.assertEqual(
            update_check.select_release_asset(assets, "Linux"),
            ("pinyin-tones-linux.zip", "https://example/linux"),
        )

    def test_parse_release_info_handles_missing_asset(self):
        release = update_check.parse_release_info(
            {
                "tag_name": "v0.2.0",
                "html_url": "https://github.com/example/release",
                "assets": [],
            },
            platform_name="Windows",
        )
        self.assertEqual(release.version, "0.2.0")
        self.assertIsNone(release.asset_name)
        self.assertIsNone(release.asset_url)

    def test_fetch_latest_release_parses_github_payload(self):
        payload = {
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/example/release",
            "published_at": "2026-06-01T00:00:00Z",
            "assets": [
                {
                    "name": "pinyin-tones-windows.zip",
                    "browser_download_url": "https://example/windows.zip",
                }
            ],
        }
        with mock.patch.object(
            update_check.urllib.request,
            "urlopen",
            return_value=FakeResponse(json.dumps(payload).encode("utf-8")),
        ):
            release = update_check.fetch_latest_release()
        self.assertEqual(release.version, "0.2.0")
        self.assertEqual(release.asset_name, "pinyin-tones-windows.zip")

    def test_should_check_for_updates_uses_interval(self):
        now = datetime(2026, 6, 2, tzinfo=timezone.utc)
        config = {
            "update_check_enabled": True,
            "update_check_interval_hours": 24,
            "last_update_check_at": (now - timedelta(hours=23)).isoformat(),
        }
        self.assertFalse(update_check.should_check_for_updates(config, now=now))
        config["last_update_check_at"] = (now - timedelta(hours=24, minutes=1)).isoformat()
        self.assertTrue(update_check.should_check_for_updates(config, now=now))

    def test_existing_download_for_release_requires_matching_existing_path(self):
        release = update_check.ReleaseInfo(
            version="0.2.0",
            tag="v0.2.0",
            html_url="https://example/release",
            asset_name="pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pinyin-tones-windows.zip"
            path.write_text("zip", encoding="utf-8")
            self.assertEqual(
                update_check.existing_download_for_release(release, "0.2.0", str(path)),
                str(path),
            )
            self.assertIsNone(
                update_check.existing_download_for_release(release, "0.1.0", str(path))
            )

    def test_check_for_updates_returns_available_state(self):
        release = update_check.ReleaseInfo(
            version="0.2.0",
            tag="v0.2.0",
            html_url="https://example/release",
            asset_name="pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with mock.patch.object(update_check, "fetch_latest_release", return_value=release):
            state = update_check.check_for_updates("0.1.0")
        self.assertEqual(state.status, "available")
        self.assertEqual(state.latest_release.version, "0.2.0")

    def test_check_for_updates_handles_no_newer_release(self):
        release = update_check.ReleaseInfo(
            version="0.1.0",
            tag="v0.1.0",
            html_url="https://example/release",
            asset_name=None,
            asset_url=None,
            published_at=None,
        )
        with mock.patch.object(update_check, "fetch_latest_release", return_value=release):
            state = update_check.check_for_updates("0.1.0")
        self.assertEqual(state.status, "up_to_date")

    def test_check_for_updates_treats_v_prefixed_equal_version_as_up_to_date(self):
        release = update_check.ReleaseInfo(
            version="1.0.0",
            tag="v1.0.0",
            html_url="https://example/release",
            asset_name="pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with mock.patch.object(update_check, "fetch_latest_release", return_value=release):
            state = update_check.check_for_updates("1.0.0")

        self.assertEqual(state.status, "up_to_date")
        self.assertEqual(state.latest_release.version, "1.0.0")

    def test_check_for_updates_handles_fetch_error(self):
        with mock.patch.object(update_check, "fetch_latest_release", side_effect=RuntimeError("boom")):
            state = update_check.check_for_updates("0.1.0")
        self.assertEqual(state.status, "error")
        self.assertEqual(state.last_error, "boom")

    def test_download_release_asset_writes_file(self):
        release = update_check.ReleaseInfo(
            version="0.2.0",
            tag="v0.2.0",
            html_url="https://example/release",
            asset_name="pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(
                update_check.urllib.request,
                "urlopen",
                return_value=FakeResponse(b"zip-content"),
            ):
                path = update_check.download_release_asset(release, temp_dir)
            self.assertTrue(Path(path).exists())
            self.assertEqual(Path(path).read_bytes(), b"zip-content")
            self.assertFalse(Path(f"{path}.part").exists())

    def test_ensure_download_dir_uses_exact_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads = Path(temp_dir) / "state" / "downloads"

            self.assertEqual(update_check.ensure_download_dir(str(downloads)), str(downloads))
            self.assertTrue(downloads.exists())

    def test_download_release_asset_rejects_path_separator_in_asset_name(self):
        release = update_check.ReleaseInfo(
            version="0.2.0",
            tag="v0.2.0",
            html_url="https://example/release",
            asset_name="../pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                update_check.download_release_asset(release, temp_dir)

    def test_download_release_asset_removes_partial_file_on_failure(self):
        release = update_check.ReleaseInfo(
            version="0.2.0",
            tag="v0.2.0",
            html_url="https://example/release",
            asset_name="pinyin-tones-windows.zip",
            asset_url="https://example/windows.zip",
            published_at=None,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(
                update_check.urllib.request,
                "urlopen",
                return_value=FailingResponse(),
            ):
                with self.assertRaises(OSError):
                    update_check.download_release_asset(release, temp_dir)

            self.assertFalse((Path(temp_dir) / "pinyin-tones-windows.zip").exists())
            self.assertFalse((Path(temp_dir) / "pinyin-tones-windows.zip.part").exists())
