"""Provider base classes and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, List

from pydantic import BaseModel

import niquests
from app.core.config import get_settings
from app.models.media import Movie, TVSeries


class DownloadResult(BaseModel):
    """A download result from a provider (movie or episode)."""

    title: str
    quality: str
    size: int
    download_url: str
    provider_name: str = ""
    source_site: str
    filename: str = ""  # Original filename from provider
    # Episode-specific fields (optional for movies)
    season: int | None = None
    episode: int | None = None


# Backward compatibility aliases
class MovieResult(DownloadResult):
    pass


class EpisodeResult(DownloadResult):
    pass


class ProviderInterface(ABC):
    """Abstract base class for DDL providers.

    All providers must implement this interface to be compatible
    with the Mirrarr provider system. Providers receive pre-fetched
    TMDB data via Movie/TVSeries objects - they do not query TMDB.
    """

    def __init__(self):
        settings = get_settings()
        self.session = niquests.AsyncSession()
        if settings.proxy:
            self.session.proxies = {"http": settings.proxy, "https": settings.proxy}

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this provider."""
        pass

    @abstractmethod
    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        """Get download links for a movie.

        Args:
            movie: The Movie object with full TMDB data.

        Returns:
            A list of MovieResult objects with available downloads.
        """
        pass

    @abstractmethod
    async def get_series_episode(
        self,
        series: TVSeries,
        season: int,
        episode: int,
    ) -> List[EpisodeResult]:
        """Get download links for a TV episode.

        Args:
            series: The TVSeries object with full TMDB data.
            season: The season number.
            episode: The episode number.

        Returns:
            A list of EpisodeResult objects with available downloads.
        """
        pass

    def get_yt_opts(self) -> dict[str, Any]:
        """Return custom yt-dlp options for this provider.

        Override this method to add custom headers, cookies, or other
        yt-dlp options specific to this provider.

        Example:
            return {
                "http_headers": {
                    "Referer": "https://example.com",
                    "User-Agent": "Custom UA",
                }
            }

        Returns:
            A dict of yt-dlp options to merge with defaults.
        """
        settings = get_settings()
        opts = {}
        if settings.proxy:
            opts["proxy"] = settings.proxy
        return opts
