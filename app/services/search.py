"""Search service for aggregating results from providers."""

from typing import List, Union

from app.providers import ProviderRegistry
from app.providers.base import MovieResult, EpisodeResult
from app.models.media import Movie, TVSeries
from app.services.tmdb import get_movie_details, get_series_details


async def get_provider_results_for_movie(
    tmdb_id: int,
) -> tuple[Movie, List[MovieResult]]:
    """Get download links from all providers for a movie.

    First fetches the Movie from TMDB, then queries all providers.

    Returns:
        Tuple of (Movie, list of MovieResult)
    """
    movie = get_movie_details(tmdb_id)
    results: List[MovieResult] = []

    for provider in ProviderRegistry.all():
        try:
            provider_results = await provider.get_movie(movie)
            results.extend(provider_results)
        except Exception as e:
            print(f"Error fetching movie from {provider.name}: {e}")

    return movie, results


async def get_provider_results_for_episode(
    tmdb_id: int,
    season: int,
    episode: int,
) -> tuple[TVSeries, List[EpisodeResult]]:
    """Get download links from all providers for a TV episode.

    First fetches the TVSeries from TMDB, then queries all providers.

    Returns:
        Tuple of (TVSeries, list of EpisodeResult)
    """
    series = get_series_details(tmdb_id)
    results: List[EpisodeResult] = []

    for provider in ProviderRegistry.all():
        try:
            provider_results = await provider.get_series_episode(
                series, season, episode
            )
            results.extend(provider_results)
        except Exception as e:
            print(f"Error fetching episode from {provider.name}: {e}")

    return series, results


def select_best_result(
    results: List[Union[MovieResult, EpisodeResult]],
) -> Union[MovieResult, EpisodeResult, None]:
    """Select the best result: highest quality first, then smallest size.

    Priority:
    1. Quality (2160p > 1080p > 720p > 480p)
    2. Within same quality, prefer smaller file size
    """
    if not results:
        return None

    quality_scores = {
        "2160p": 4,
        "4k": 4,
        "1080p": 3,
        "720p": 2,
        "480p": 1,
    }

    def score(result: Union[MovieResult, EpisodeResult]) -> tuple[int, float]:
        """Return (quality_score, -size_mb) for sorting.

        Higher quality score is better.
        Negative size means smaller files sort first when reversed.
        """
        quality = result.quality.split()[0].lower() if result.quality else "480p"
        q_score = quality_scores.get(quality, 0)
        # Return tuple: (quality descending, size ascending)
        return (q_score, -result.size_mb)

    # Sort by quality (desc), then by size (asc via negative)
    return max(results, key=score)
