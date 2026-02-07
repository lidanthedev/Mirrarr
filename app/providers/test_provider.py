"""Test provider for testing multiple provider display."""

import asyncio
from typing import List

from app.providers.base import ProviderInterface, MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries


class TestProvider(ProviderInterface):
    """A second test provider for testing provider grouping.

    Returns different quality options than DummyProvider.
    """

    @property
    def name(self) -> str:
        return "TestProvider"

    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        """Return test movie download links."""
        await asyncio.sleep(3)

        return [
            MovieResult(
                title=movie.title,
                quality="1080p REMUX",
                size_mb=25000.0,
                download_url=f"https://test-provider.com/movie/{movie.id}/remux",
                source_site=self.name,
                filename=f"{movie.title}.1080p.REMUX.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="1080p BluRay",
                size_mb=12000.0,
                download_url=f"https://test-provider.com/movie/{movie.id}/bluray",
                source_site=self.name,
                filename=f"{movie.title}.1080p.BluRay.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="720p WEB-DL",
                size_mb=3500.0,
                download_url=f"https://test-provider.com/movie/{movie.id}/720p",
                source_site=self.name,
                filename=f"{movie.title}.720p.WEB-DL.mkv",
            ),
        ]

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
                filename=f"{series.title}.S{season:02d}E{episode:02d}.1080p.AMZN.WEB-DL.mkv",
            ),
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="720p WEB-DL",
                size_mb=800.0,
                download_url=f"https://test-provider.com/tv/{series.id}/s{season}e{episode}/720p",
                source_site=self.name,
                filename=f"{series.title}.S{season:02d}E{episode:02d}.720p.WEB-DL.mkv",
            ),
        ]
