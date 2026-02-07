"""A111477 provider for https://a.111477.xyz/."""

import logging
import niquests
import re
from typing import List

from app.providers.base import ProviderInterface, MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries
from bs4 import BeautifulSoup
from typing import NamedTuple
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://a.111477.xyz/"
ALLOWED_EXTENSIONS = video_extensions = (
    # Common & Modern
    "mp4",
    "m4v",
    "mkv",
    "webm",
    "mov",
    "avi",
    "wmv",
    # High Definition / Transport Streams
    "mts",
    "m2ts",
    "ts",
    "avchd",
    # Legacy / Mobile
    "flv",
    "vob",
    "ogv",
    "3gp",
    "3g2",
    "mjp",
    "m1v",
    "m2v",
    # Professional / Flash / Other
    "f4v",
    "swf",
    "asf",
    "qt",
)


# Typed Named Tuple for file entries
class FileEntry(NamedTuple):
    name: str
    path: str
    size: float


async def get_directory_contents(target_url):
    """Parse directory contents from table-based HTML format.

    Format:
    <table id="fileTable">
        <tr data-entry="true" data-name="foo" data-url="/foo/">
            <td class="size" data-sort="-1">-</td>
        </tr>
    </table>
    """
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = await niquests.aget(target_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all table rows with data-entry="true"
        file_entries = soup.find_all("tr", attrs={"data-entry": "true"})

        for entry in file_entries:
            # Get name and URL from data attributes
            name = entry.get("data-name", "")
            url_path = entry.get("data-url", "")

            if name and url_path:
                path = urljoin(target_url, url_path)

                # Get size from td.size data-sort attribute (byte value)
                size_td = entry.find("td", class_="size")
                size_sort = size_td.get("data-sort", "-1") if size_td else "-1"

                try:
                    size = float(size_sort)
                    if size < 0:
                        size = 0.0
                except ValueError:
                    size = 0.0

                results.append(FileEntry(name=name, path=path, size=size))

        return results

    except Exception as e:
        print(f"Error: {e}")
        return []


class A111477Provider(ProviderInterface):
    """A111477 provider for https://a.111477.xyz/."""

    @property
    def name(self) -> str:
        return "A111477Provider"

    async def get_directory(self, directory: str) -> List[FileEntry]:
        """Return directory contents."""
        return await get_directory_contents(directory)

    async def get_movie_entries(self) -> List[FileEntry]:
        """Return list of movies."""
        return await get_directory_contents(f"{BASE_URL}/movies")

    async def get_tv_entries(self) -> List[FileEntry]:
        """Return list of TV series."""
        return await get_directory_contents(f"{BASE_URL}/tvs")

    async def get_movie_entries_by_name(self, name: str) -> List[FileEntry]:
        """Return list of movie files by name.

        Movies can be:
        1. Directly in /movies as files (e.g., KPop.Demon.Hunters.2025.1080p.WEB.h264-EDITH.mkv)
        2. Inside a folder (e.g., /movies/The Matrix (1999)/ containing .mkv/.mp4 files)
        """
        movie_entries = await self.get_movie_entries()
        results = []
        name_lower = name.lower()

        for entry in movie_entries:
            entry_name_lower = entry.name.lower()

            # Check if it's a direct video file that matches the movie name
            if entry.name.endswith(ALLOWED_EXTENSIONS):
                # Check if movie name appears in the filename
                if name_lower in entry_name_lower or self._normalize_name(
                    name_lower
                ) in self._normalize_name(entry_name_lower):
                    results.append(entry)
            else:
                # It's a folder - check if folder name matches movie name
                if name_lower in entry_name_lower or self._normalize_name(
                    name_lower
                ) in self._normalize_name(entry_name_lower):
                    # Get files inside the folder
                    folder_contents = await get_directory_contents(entry.path)
                    for file_entry in folder_contents:
                        if file_entry.name.endswith(ALLOWED_EXTENSIONS):
                            results.append(file_entry)

        return results

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for fuzzy matching by removing special chars."""

        # Remove year in parentheses, dots, dashes, underscores
        name = re.sub(r"\(\d{4}\)", "", name)
        name = re.sub(r"[.\-_]", " ", name)
        name = re.sub(r"\s+", " ", name)
        return name.strip().lower()

    def get_quality_from_name(self, name: str) -> str:
        """Return quality from name."""
        if "2160p" in name:
            return "2160p"
        elif "1080p" in name:
            return "1080p"
        elif "720p" in name:
            return "720p"
        return "Unknown"

    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        """Return movie download links."""
        try:
            movie_entries = await self.get_movie_entries_by_name(movie.title)
            results = []
            for movie_entry in movie_entries:
                if movie_entry.name.endswith(ALLOWED_EXTENSIONS):
                    logger.info(f"Movie entry: {movie_entry}")
                    results.append(
                        MovieResult(
                            title=movie.title,
                            quality=self.get_quality_from_name(movie_entry.name),
                            size_mb=movie_entry.size / 1024 / 1024,
                            download_url=movie_entry.path,
                            source_site=self.name,
                        )
                    )
            return results
        except Exception as e:
            logger.warning(f"Error fetching movie from {self.name}", exc_info=e)
            return []

    async def get_series_entries_by_name(self, name: str) -> List[FileEntry]:
        """Return list of series folder entries by name.

        Series can be:
        1. A folder like /shows/Breaking Bad/
        2. Inside that folder, episodes directly or season folders
        """
        tv_entries = await self.get_tv_entries()
        name_lower = name.lower()

        for entry in tv_entries:
            entry_name_lower = entry.name.lower()

            # Check if folder name matches series name
            if name_lower in entry_name_lower or self._normalize_name(
                name_lower
            ) in self._normalize_name(entry_name_lower):
                return [entry]

        return []

    async def get_episode_files(
        self,
        series_path: str,
        season: int,
        episode: int,
    ) -> List[FileEntry]:
        """Find episode files for a specific season and episode.

        Structure can be:
        1. /shows/Series Name/Season X/ - episodes in season folder
        2. /shows/Series Name/ - episodes directly in series folder
        """
        results = []
        folder_contents = await get_directory_contents(series_path)

        # Look for season folder first (e.g., "Season 1", "Season 01", "S01")
        season_patterns = [
            f"season {season}",
            f"season {season:02d}",
            f"s{season:02d}",
            f"s{season}",
        ]

        for entry in folder_contents:
            entry_name_lower = entry.name.lower()

            # Check if this is a season folder
            for pattern in season_patterns:
                if pattern in entry_name_lower:
                    # Found season folder, get episodes from it
                    season_contents = await get_directory_contents(entry.path)
                    for ep_entry in season_contents:
                        if self._matches_episode(ep_entry.name, season, episode):
                            results.append(ep_entry)
                    break

            # Also check if episodes are directly in series folder
            if entry.name.endswith((".mkv", ".mp4", ".avi")):
                if self._matches_episode(entry.name, season, episode):
                    results.append(entry)

        return results

    def _matches_episode(self, filename: str, season: int, episode: int) -> bool:
        """Check if filename matches the season and episode number."""
        filename_lower = filename.lower()

        # Common patterns: S01E01, s01e01, 1x01, etc.
        patterns = [
            rf"s{season:02d}e{episode:02d}",
            rf"s{season}e{episode}",
            rf"{season}x{episode:02d}",
            rf"{season}x{episode}",
            rf"season\s*{season}.*episode\s*{episode}",
        ]

        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return True

        return False

    async def get_series_episode(
        self,
        series: TVSeries,
        season: int,
        episode: int,
    ) -> List[EpisodeResult]:
        """Return episode download links from A111477."""
        try:
            # Find the series folder
            series_entries = await self.get_series_entries_by_name(series.title)

            if not series_entries:
                logger.info(f"Series not found: {series.title}")
                return []

            results = []
            for series_entry in series_entries:
                # Get episode files for this season/episode
                episode_files = await self.get_episode_files(
                    series_entry.path, season, episode
                )

                for ep_file in episode_files:
                    if ep_file.name.endswith(ALLOWED_EXTENSIONS):
                        logger.info(f"Episode entry: {ep_file}")
                        results.append(
                            EpisodeResult(
                                title=f"{series.title} S{season:02d}E{episode:02d}",
                                season=season,
                                episode=episode,
                                quality=self.get_quality_from_name(ep_file.name),
                                size_mb=ep_file.size / 1024 / 1024
                                if ep_file.size
                                else 0.0,
                                download_url=ep_file.path,
                                source_site=self.name,
                            )
                        )

            return results
        except Exception as e:
            logger.warning(f"Error fetching episode from {self.name}", exc_info=e)
            return []
