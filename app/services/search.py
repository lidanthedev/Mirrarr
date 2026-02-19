"""Search service for aggregating results from providers."""

import asyncio
import logging
from typing import List, Union

from app.providers import ProviderRegistry
from app.providers.base import MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries
from app.services.tmdb import get_movie_details, get_series_details
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def get_provider_results_for_movie(
    tmdb_id: int,
) -> tuple[Movie, List[MovieResult]]:
    """Get download links from all providers for a movie.

    First fetches the Movie from TMDB, then queries all providers concurrently.

    Returns:
        Tuple of (Movie, list of MovieResult)
    """
    settings = get_settings()
    timeout = settings.provider_timeout
    movie = await get_movie_details(tmdb_id)
    providers = ProviderRegistry.all()

    async def fetch_from_provider(provider):
        try:
            return await asyncio.wait_for(provider.get_movie(movie), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout fetching movie from {provider.name} after {timeout}s"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching movie from {provider.name}: {e}", exc_info=e)
            return []

    provider_results = await asyncio.gather(
        *[fetch_from_provider(p) for p in providers]
    )

    results: List[MovieResult] = []
    for result_list in provider_results:
        results.extend(result_list)

    return movie, results


async def get_provider_results_for_episode(
    tmdb_id: int,
    season: int,
    episode: int,
) -> tuple[TVSeries, List[EpisodeResult]]:
    """Get download links from all providers for a TV episode.

    First fetches the TVSeries from TMDB, then queries all providers concurrently.

    Returns:
        Tuple of (TVSeries, list of EpisodeResult)
    """
    settings = get_settings()
    timeout = settings.provider_timeout
    series = await get_series_details(tmdb_id)
    providers = ProviderRegistry.all()

    async def fetch_from_provider(provider):
        try:
            return await asyncio.wait_for(
                provider.get_series_episode(series, season, episode), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout fetching episode from {provider.name} after {timeout}s"
            )
            return []
        except Exception as e:
            logger.error(
                f"Error fetching episode from {provider.name}: {e}", exc_info=e
            )
            return []

    provider_results = await asyncio.gather(
        *[fetch_from_provider(p) for p in providers]
    )

    results: List[EpisodeResult] = []
    for result_list in provider_results:
        results.extend(result_list)

    return series, results


async def get_single_provider_results_for_movie(
    tmdb_id: int,
    provider_name: str,
) -> tuple[Movie, List[MovieResult]]:
    """Get download links from a single provider for a movie.

    Returns:
        Tuple of (Movie, list of MovieResult)
    """
    settings = get_settings()
    timeout = settings.provider_timeout
    movie = await get_movie_details(tmdb_id)
    results: List[MovieResult] = []

    provider = ProviderRegistry.get(provider_name)
    if provider:
        try:
            provider_results = await asyncio.wait_for(
                provider.get_movie(movie), timeout=timeout
            )
            results.extend(provider_results)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout fetching movie from {provider.name} after {timeout}s"
            )
        except Exception as e:
            logger.error(f"Error fetching movie from {provider.name}: {e}", exc_info=e)

    return movie, results


async def get_single_provider_results_for_episode(
    tmdb_id: int,
    season: int,
    episode: int,
    provider_name: str,
) -> tuple[TVSeries, List[EpisodeResult]]:
    """Get download links from a single provider for a TV episode.

    Returns:
        Tuple of (TVSeries, list of EpisodeResult)
    """
    settings = get_settings()
    timeout = settings.provider_timeout
    series = await get_series_details(tmdb_id)
    results: List[EpisodeResult] = []

    provider = ProviderRegistry.get(provider_name)
    if provider:
        try:
            provider_results = await asyncio.wait_for(
                provider.get_series_episode(series, season, episode), timeout=timeout
            )
            results.extend(provider_results)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout fetching episode from {provider.name} after {timeout}s"
            )
        except Exception as e:
            logger.error(
                f"Error fetching episode from {provider.name}: {e}", exc_info=e
            )

    return series, results


def select_best_result(
    results: List[Union[MovieResult, EpisodeResult]],
) -> Union[MovieResult, EpisodeResult, None]:
    """Select the best result: highest quality first, then smallest size.

    Priority:
    1. Preferred Provider (if configured and found)
    2. Quality (Limit to max quality, 2160p > 1080p > 720p > 480p)
    3. Within same quality, prefer smaller file size
    """
    if not results:
        return None

    settings = get_settings()
    pref_provider = settings.preferred_provider
    q_limit = settings.quality_limit.lower() if settings.quality_limit else "2160p"

    quality_scores = {
        "2160p": 4,
        "4k": 4,
        "1080p": 3,
        "720p": 2,
        "480p": 1,
    }

    limit_score = quality_scores.get(q_limit, 4)

    # Filter results by quality limit
    filtered_results = []
    for r in results:
        quality = r.quality.lower() if r.quality else "480p"
        if "2160" in quality or "4k" in quality:
            res_score = 4
        elif "1080" in quality:
            res_score = 3
        elif "720" in quality:
            res_score = 2
        else:
            res_score = 1
        
        if res_score <= limit_score:
            filtered_results.append(r)

    if not filtered_results:
        return None

    def score(result: Union[MovieResult, EpisodeResult]) -> tuple[int, int, float]:
        """Return (is_preferred, quality_score, -size_mb) for sorting.

        Higher is_preferred is better.
        Higher quality score (up to limit) is better.
        Negative size means smaller files sort first when reversed.
        """
        is_pref = 1 if pref_provider and result.provider_name == pref_provider else 0

        # Extract quality string and normalize
        quality = result.quality.lower() if result.quality else "480p"
        if "2160" in quality or "4k" in quality:
            q_score = 4
        elif "1080" in quality:
            q_score = 3
        elif "720" in quality:
            q_score = 2
        else:
            q_score = 1

        return (is_pref, q_score, -result.size)

    # Sort and pick best from filtered results
    return max(filtered_results, key=score)
