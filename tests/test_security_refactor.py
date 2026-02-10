import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.api.routes_api import queue_download, DownloadRequest
from app.services.download_manager import _rename_downloaded_file
from app.providers.directory_list_provider import DirectoryListProvider

# --- Test 1: SSRF Validation ---


@pytest.mark.anyio
async def test_queue_download_ssrf():
    # Valid URL (http)
    req_valid = DownloadRequest(url="http://example.com/video.mp4")
    with patch(
        "app.services.download_manager.manager.add_download", return_value="123"
    ) as mock_add:
        res = await queue_download(req_valid)
        assert res["id"] == "123"
        mock_add.assert_called_once()

    # Valid URL (https)
    req_valid_https = DownloadRequest(url="https://example.com/video.mp4")
    with patch(
        "app.services.download_manager.manager.add_download", return_value="124"
    ) as mock_add:
        res = await queue_download(req_valid_https)
        assert res["id"] == "124"

    # Invalid URL (ftp)
    req_invalid = DownloadRequest(url="ftp://example.com/video.mp4")
    with pytest.raises(HTTPException) as excinfo:
        await queue_download(req_invalid)
    assert excinfo.value.status_code == 400
    assert "Invalid URL scheme" in excinfo.value.detail

    # Invalid URL (file)
    req_invalid_file = DownloadRequest(url="file:///etc/passwd")
    with pytest.raises(HTTPException) as excinfo:
        await queue_download(req_invalid_file)
    assert excinfo.value.status_code == 400


# --- Test 2: Path Traversal ---


def test_rename_path_traversal():
    with patch("os.path.exists", return_value=True), patch("shutil.move"):
        # Case 1: Traversal attempt
        # os.path.basename("../../etc/passwd") -> "passwd"
        res = _rename_downloaded_file("/downloads/video.mp4", "../../etc/passwd")
        assert res is not None
        assert res == "/downloads/passwd.mp4"

        # Case 2: Special characters
        # "foo/bar" -> basename "bar"
        res = _rename_downloaded_file("/downloads/video.mp4", "foo/bar;rm -rf")
        # basename -> "bar;rm -rf"
        # regex sub -> "bar_rm_-rf" (underscore replaces semicolon and space)
        assert res is not None
        assert res == "/downloads/bar_rm_-rf.mp4"

        # Case 3: Empty checking
        res = _rename_downloaded_file("/downloads/video.mp4", "/")
        # basename -> "" -> None
        assert res is None


# --- Test 3: Directory Provider Regex coverage ---


class TestProvider(DirectoryListProvider):
    @property
    def name(self):
        return "Test"

    @property
    def base_url(self):
        return ""

    @property
    def movies_path(self):
        return ""

    @property
    def tv_path(self):
        return ""

    async def _parse_directory_html(self, html, base_url):
        return []


def test_matches_episode():
    provider = TestProvider()

    # Exact matches
    assert provider._matches_episode("Show.S01E01.mp4", 1, 1)
    assert provider._matches_episode("Show.s01e01.mkv", 1, 1)
    assert provider._matches_episode("Show.1x01.avi", 1, 1)

    # Boundary checks
    assert not provider._matches_episode("Show.S01E010.mp4", 1, 1)
    assert not provider._matches_episode("Show.S010E01.mp4", 1, 1)

    # Season match checks
    assert provider._matches_episode("Show Season 1 Episode 1.mp4", 1, 1)


def test_quality_cam_false_positives():
    provider = TestProvider()

    # True positives
    assert provider.get_quality_from_name("Movie.CAM.mp4") == "CAM"
    assert provider.get_quality_from_name("Movie.HDCAM.mp4") == "CAM"
    assert provider.get_quality_from_name("Movie.hdcam.mp4") == "CAM"

    # False positives
    assert provider.get_quality_from_name("Camera_Shy.mp4") == "Unknown"
    # "Webcam" contains "cam", should NOT match CAM. It currently matches WEB due to "web" in name.
    # To test CAM exclusion specifically, use something without "web".
    assert provider.get_quality_from_name("Scam_Artist.mp4") == "Unknown"
    assert provider.get_quality_from_name("Dreamcatcher.mp4") == "Unknown"
