"""Dummy provider for testing the UI flow."""

from niquests import Response
from typing import Any
import niquests
from cachetools import TTLCache
import asyncio
from typing import List

from app.providers.base import ProviderInterface, MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries

SECRET_KEY_MOVIES = "LTVlZTA5MTAw"
SECRET_KEY_TV = "NGFmNjhjZDg="

cache = TTLCache(maxsize=100, ttl=1800)


class RiveStreamProvider(ProviderInterface):
    """A dummy provider that returns fake download links.

    Useful for testing the UI without real DDL sources.
    """

    @property
    def name(self) -> str:
        return "RiveStreamProvider"

    async def get_services(self) -> List[str]:
        """Return list of services."""
        if "services" in cache:
            return cache["services"]

        response: Response = await niquests.aget(
            "https://rivestream.org/api/backendfetch?requestID=VideoProviderServices&secretKey=rive&proxyMode=noProxy"
        )
        result = response.json()["data"]
        cache["services"] = result
        return result

    async def get_movies_with_service(
        self, movie: Movie, service: str
    ) -> List[MovieResult]:
        """Return list of movies with a service."""
        cache_key = f"movies-{movie.id}-{service}"
        if cache_key in cache:
            return cache[cache_key]

        params = {
            "requestID": "movieVideoProvider",
            "id": movie.id,
            "service": service,
            "secretKey": SECRET_KEY_MOVIES,
            "proxyMode": "noProxy",
        }
        response: Response = await niquests.aget(
            "https://rivestream.org/api/backendfetch", params=params
        )
        data = response.json()["data"]
        if data is None or "sources" not in data:
            return []
        sources = data["sources"]
        movies = []
        for source in sources:
            movies.append(
                MovieResult(
                    provider_name=self.name,
                    title=movie.title,
                    download_url=source["url"],
                    quality=f"{source['quality']}p-{source['format']}",
                    size=source.get("size", 0),
                    source_site=self.name,
                    filename=f"{movie.title} - {source['quality']}p - {service}.{source['format']}",
                )
            )
        cache[cache_key] = movies
        return movies

    async def get_movie_from_all_services(self, movie: Movie) -> List[MovieResult]:
        """Return list of movies from all services."""
        services = await self.get_services()

        tasks = [self.get_movies_with_service(movie, service) for service in services]
        results = await asyncio.gather(*tasks)

        movies = []
        for result in results:
            if result is None:
                continue
            movies.extend(result)
        return movies

    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        """Return dummy movie download links."""

        return await self.get_movie_from_all_services(movie)

    async def get_series_episode_with_service(
        self, series: TVSeries, season: int, episode: int, service: str
    ) -> List[EpisodeResult]:
        """Return list of episodes with a service."""
        cache_key = f"series-{series.id}-s{season}-e{episode}-{service}"
        if cache_key in cache:
            return cache[cache_key]

        params = {
            "requestID": "tvVideoProvider",
            "id": series.id,
            "season": season,
            "episode": episode,
            "service": service,
            "secretKey": SECRET_KEY_TV,
            "proxyMode": "noProxy",
        }
        response: Response = await niquests.aget(
            "https://rivestream.org/api/backendfetch", params=params
        )
        try:
            data = response.json()["data"]
        except Exception:
            print(f"Error decoding JSON from {service}: {response.text}")
            return []
        if data is None or "sources" not in data:
            return []
        sources = data["sources"]
        episodes = []
        for source in sources:
            episodes.append(
                EpisodeResult(
                    provider_name=self.name,
                    title=f"{series.title} S{season:02d}E{episode:02d}",
                    season=season,
                    episode=episode,
                    download_url=source["url"],
                    quality=f"{source['quality']}p-{source['format']}",
                    size=source.get("size", 0),
                    source_site=self.name,
                    filename=f"{series.title} S{season:02d}E{episode:02d} - {source['quality']}p - {service}.{source['format']}",
                )
            )
        cache[cache_key] = episodes
        return episodes

    async def get_series_episode_from_all_services(
        self, series: TVSeries, season: int, episode: int
    ) -> List[EpisodeResult]:
        """Return list of episodes from all services."""
        services = await self.get_services()

        tasks = [
            self.get_series_episode_with_service(series, season, episode, service)
            for service in services
        ]
        results = await asyncio.gather(*tasks)

        episodes = []
        for result in results:
            if result is None:
                continue
            episodes.extend(result)
        return episodes

    async def get_series_episode(
        self,
        series: TVSeries,
        season: int,
        episode: int,
    ) -> List[EpisodeResult]:
        """Return episode download links from all services."""
        return await self.get_series_episode_from_all_services(series, season, episode)

    def get_yt_opts(self) -> dict[str, Any]:
        return {
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://rivestream.org/",
                "Accept-Language": "en-US,en;q=0.9",
            }
        }
