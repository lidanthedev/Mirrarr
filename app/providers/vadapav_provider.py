"""Vadapav provider."""

import logging
import niquests
import asyncio
from typing import List

from app.providers.base import ProviderInterface, MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries
from bs4 import BeautifulSoup
from collections import namedtuple
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = "https://vadapav.mov"

# Updated Named Tuple to include size
FileEntry = namedtuple("FileEntry", ["name", "path", "size"])


async def get_directory_contents(target_url):
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = await niquests.aget(target_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        file_entries = soup.find_all("li", class_="file-entry")

        for entry in file_entries:
            # 1. Get the Name and Link
            link_tag = entry.find("a", class_="directory-entry")

            if link_tag:
                name = link_tag.get_text(strip=True)
                path = urljoin(target_url, link_tag.get("href"))

                # 2. Get the Size
                # We find the div that contains the name,
                # then look for the next div sibling which holds the size.
                name_div = entry.find("div", class_="name-div")
                size_div = name_div.find_next_sibling("div")

                size = size_div.get_text(strip=True) if size_div else "-"
                if size == "-":
                    size = 0.0
                else:
                    size = float(size)

                results.append(FileEntry(name=name, path=path, size=size))

        return results

    except Exception as e:
        print(f"Error: {e}")
        return []


class VadapavProvider(ProviderInterface):
    """Vadapav provider."""

    @property
    def name(self) -> str:
        return "VadapavProvider"

    async def get_directory(self, directory: str) -> List[FileEntry]:
        """Return directory contents."""
        return await get_directory_contents(directory)

    async def get_movie_entries(self) -> List[FileEntry]:
        """Return list of movies."""
        return await get_directory_contents(f"{BASE_URL}/movies")

    async def get_tv_entries(self) -> List[FileEntry]:
        """Return list of TV series."""
        return await get_directory_contents(f"{BASE_URL}/shows")

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
            if entry.name.endswith((".mkv", ".mp4", ".avi")):
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
                        if file_entry.name.endswith((".mkv", ".mp4", ".avi")):
                            results.append(file_entry)

        return results

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for fuzzy matching by removing special chars."""
        import re

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
                if movie_entry.name.endswith((".mkv", ".mp4", ".avi")):
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

    async def get_series_episode(
        self,
        series: TVSeries,
        season: int,
        episode: int,
    ) -> List[EpisodeResult]:
        """Return test episode download links."""
        await asyncio.sleep(3)

        return [
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="1080p AMZN WEB-DL",
                size_mb=2500.0,
                download_url=f"https://test-provider.com/tv/{series.id}/s{season}e{episode}/amzn",
                source_site=self.name,
            ),
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="720p WEB-DL",
                size_mb=800.0,
                download_url=f"https://test-provider.com/tv/{series.id}/s{season}e{episode}/720p",
                source_site=self.name,
            ),
        ]
