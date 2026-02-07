"""Dummy provider for testing the UI flow."""

from typing import List

from app.providers.base import ProviderInterface, MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries


class DummyProvider(ProviderInterface):
    """A dummy provider that returns fake download links.

    Useful for testing the UI without real DDL sources.
    """

    @property
    def name(self) -> str:
        return "DummyProvider"

    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        """Return dummy movie download links."""
        return [
            MovieResult(
                title=movie.title,
                quality="2160p UHD",
                size_mb=15000.0,
                download_url=f"https://example.com/movie/{movie.id}/2160p",
                source_site=self.name,
                filename=f"{movie.title}.2160p.UHD.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="1080p BluRay",
                size_mb=8000.0,
                download_url=f"https://example.com/movie/{movie.id}/1080p",
                source_site=self.name,
                filename=f"{movie.title}.1080p.BluRay.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="1080p WEB-DL",
                size_mb=4500.0,
                download_url=f"https://example.com/movie/{movie.id}/1080p-web",
                source_site=self.name,
                filename=f"{movie.title}.1080p.WEB-DL.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="720p WEB-DL",
                size_mb=2500.0,
                download_url=f"https://example.com/movie/{movie.id}/720p",
                source_site=self.name,
                filename=f"{movie.title}.720p.WEB-DL.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="480p HDTV",
                size_mb=700.0,
                download_url=f"https://example.com/movie/{movie.id}/480p",
                source_site=self.name,
                filename=f"{movie.title}.480p.HDTV.mkv",
            ),
        ]

    async def get_series_episode(
        self,
        series: TVSeries,
        season: int,
        episode: int,
    ) -> List[EpisodeResult]:
        """Return dummy episode download links."""
        return [
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="1080p WEB-DL",
                size_mb=1200.0,
                download_url=f"https://example.com/tv/{series.id}/s{season}e{episode}/1080p",
                source_site=self.name,
                filename=f"{series.title}.S{season:02d}E{episode:02d}.1080p.WEB-DL.mkv",
            ),
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="720p HDTV",
                size_mb=450.0,
                download_url=f"https://example.com/tv/{series.id}/s{season}e{episode}/720p",
                source_site=self.name,
                filename=f"{series.title}.S{season:02d}E{episode:02d}.720p.HDTV.mkv",
            ),
        ]
