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
                size=15728640000,
                download_url=f"https://example.com/movie/{movie.id}/2160p",
                source_site=self.name,
                filename=f"{movie.title}.2160p.UHD.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="1080p BluRay",
                size=8388608000,
                download_url=f"https://example.com/movie/{movie.id}/1080p",
                source_site=self.name,
                filename=f"{movie.title}.1080p.BluRay.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="1080p WEB-DL",
                size=4718592000,
                download_url=f"https://example.com/movie/{movie.id}/1080p-web",
                source_site=self.name,
                filename=f"{movie.title}.1080p.WEB-DL.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="720p WEB-DL",
                size=2621440000,
                download_url=f"https://example.com/movie/{movie.id}/720p",
                source_site=self.name,
                filename=f"{movie.title}.720p.WEB-DL.mkv",
            ),
            MovieResult(
                title=movie.title,
                quality="480p HDTV",
                size=734003200,
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
                size=1258291200,
                download_url=f"https://example.com/tv/{series.id}/s{season}e{episode}/1080p",
                source_site=self.name,
                filename=f"{series.title}.S{season:02d}E{episode:02d}.1080p.WEB-DL.mkv",
            ),
            EpisodeResult(
                title=f"{series.title} S{season:02d}E{episode:02d}",
                season=season,
                episode=episode,
                quality="720p HDTV",
                size=471859200,
                download_url=f"https://example.com/tv/{series.id}/s{season}e{episode}/720p",
                source_site=self.name,
                filename=f"{series.title}.S{season:02d}E{episode:02d}.720p.HDTV.mkv",
            ),
        ]
