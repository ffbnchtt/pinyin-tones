"""GitHub release update helpers."""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pinyin_app.version import is_newer_version, normalize_version

logger = logging.getLogger("pinyin_app")

DEFAULT_REPO = "ffbnchtt/pinyin-tones"
DEFAULT_UPDATE_CHECK_INTERVAL_HOURS = 24
DEFAULT_TIMEOUT_SECONDS = 3.0
RELEASES_API_TEMPLATE = "https://api.github.com/repos/{repo}/releases/latest"
RELEASES_PAGE_TEMPLATE = "https://github.com/{repo}/releases/latest"
DOWNLOAD_ASSET_NAMES = {
    "windows": "pinyin-tones-windows.zip",
    "macos": "pinyin-tones-macos.zip",
    "linux": "pinyin-tones-linux.zip",
}


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    html_url: str
    asset_name: Optional[str]
    asset_url: Optional[str]
    published_at: Optional[str]


@dataclass
class UpdateState:
    status: str = "idle"
    latest_release: Optional[ReleaseInfo] = None
    downloaded_path: Optional[str] = None
    last_error: Optional[str] = None


def current_platform_slug(system_name: str | None = None) -> str:
    """Map runtime platform names to a stable asset suffix."""
    name = (system_name or platform.system()).strip().lower()
    if name.startswith("win"):
        return "windows"
    if name in {"darwin", "mac", "macos"}:
        return "macos"
    return "linux"


def releases_api_url(repo: str = DEFAULT_REPO) -> str:
    return RELEASES_API_TEMPLATE.format(repo=repo)


def releases_page_url(repo: str = DEFAULT_REPO) -> str:
    return RELEASES_PAGE_TEMPLATE.format(repo=repo)


def build_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "pinyin-tones-update-check",
        },
    )


def select_release_asset(
    assets: list[dict[str, Any]],
    platform_name: str | None = None,
) -> tuple[Optional[str], Optional[str]]:
    """Pick the expected asset name/url for the current platform."""
    expected_name = DOWNLOAD_ASSET_NAMES[current_platform_slug(platform_name)]
    for asset in assets:
        name = str(asset.get("name", "")).strip()
        if name.lower() != expected_name.lower():
            continue
        url = asset.get("browser_download_url")
        if not url:
            continue
        return name, str(url)
    return None, None


def parse_release_info(payload: dict[str, Any], platform_name: str | None = None) -> Optional[ReleaseInfo]:
    """Parse GitHub release JSON into a compact release object."""
    tag = str(payload.get("tag_name", "")).strip()
    html_url = str(payload.get("html_url", "")).strip()
    version = normalize_version(tag)
    if not version or not html_url:
        return None
    asset_name, asset_url = select_release_asset(payload.get("assets") or [], platform_name)
    return ReleaseInfo(
        version=version,
        tag=tag,
        html_url=html_url,
        asset_name=asset_name,
        asset_url=asset_url,
        published_at=payload.get("published_at"),
    )


def fetch_latest_release(
    repo: str = DEFAULT_REPO,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Optional[ReleaseInfo]:
    """Fetch the latest stable GitHub release for the configured repo."""
    try:
        with urllib.request.urlopen(build_request(releases_api_url(repo)), timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.info("No releases found for %s", repo)
            return None
        raise
    return parse_release_info(payload)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_isoformat() -> str:
    return utcnow().isoformat()


def parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse ISO-8601 strings or epoch timestamps to UTC datetimes."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def should_check_for_updates(config: dict[str, Any], now: Optional[datetime] = None) -> bool:
    """Return True when the configured interval has elapsed."""
    if not bool(config.get("update_check_enabled", True)):
        return False
    interval_hours = float(config.get("update_check_interval_hours", DEFAULT_UPDATE_CHECK_INTERVAL_HOURS))
    last_checked = parse_timestamp(config.get("last_update_check_at"))
    if last_checked is None:
        return True
    reference = now or utcnow()
    return reference - last_checked >= timedelta(hours=interval_hours)


def mark_update_check(config: dict[str, Any], when: Optional[datetime] = None) -> None:
    """Persist the most recent update-check timestamp."""
    config["last_update_check_at"] = (when or utcnow()).isoformat()


def existing_download_for_release(
    release: Optional[ReleaseInfo],
    downloaded_version: str | None,
    downloaded_path: str | None,
) -> Optional[str]:
    """Return an existing download path if it still matches the release."""
    if release is None or not downloaded_path or not downloaded_version:
        return None
    if downloaded_version != release.version:
        return None
    if not os.path.exists(downloaded_path):
        return None
    return downloaded_path


def check_for_updates(
    current_version: str,
    downloaded_version: str | None = None,
    downloaded_path: str | None = None,
    repo: str = DEFAULT_REPO,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> UpdateState:
    """Fetch release information and compare it with the current version."""
    try:
        release = fetch_latest_release(repo=repo, timeout=timeout)
    except Exception as exc:
        logger.exception("Update check failed")
        return UpdateState(status="error", last_error=str(exc))

    if release is None:
        return UpdateState(status="no_release")
    if not is_newer_version(release.version, current_version):
        return UpdateState(status="up_to_date", latest_release=release)
    return UpdateState(
        status="available",
        latest_release=release,
        downloaded_path=existing_download_for_release(release, downloaded_version, downloaded_path),
    )


def ensure_download_dir(base_dir: str) -> str:
    """Create the update download directory if needed."""
    path = os.path.join(base_dir, "downloads")
    os.makedirs(path, exist_ok=True)
    return path


def download_release_asset(release: ReleaseInfo, download_dir: str, timeout: float = 30.0) -> str:
    """Download the selected asset for a release and return its local path."""
    if not release.asset_name or not release.asset_url:
        raise ValueError("Release does not include a compatible downloadable asset")
    os.makedirs(download_dir, exist_ok=True)
    destination = os.path.join(download_dir, release.asset_name)
    request = build_request(release.asset_url)
    with urllib.request.urlopen(request, timeout=timeout) as response, open(destination, "wb") as handle:
        shutil.copyfileobj(response, handle)
    return destination


def open_release_page(url: str) -> bool:
    """Open the release page in the default browser."""
    return bool(webbrowser.open(url))


def open_download_folder(path: str) -> None:
    """Open the folder containing a downloaded update."""
    folder = Path(path).resolve().parent if Path(path).suffix else Path(path).resolve()
    system = platform.system()
    if system == "Windows" and hasattr(os, "startfile"):
        os.startfile(str(folder))  # type: ignore[attr-defined]
        return
    if system == "Darwin":
        subprocess.Popen(["open", str(folder)])
        return
    subprocess.Popen(["xdg-open", str(folder)])
