"""TMDB service for searching and fetching movie/series details."""

from functools import cache
from typing import List, Optional
from enum import Enum

import tmdbsimple as tmdb
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.media import Movie, TVSeries, Season, Episode

# Initialize TMDB
settings = get_settings()
tmdb.API_KEY = settings.tmdb_api_key


class MediaType(str, Enum):
    """Media type for search."""

    MOVIE = "movie"
    SERIES = "tv"
    ALL = "all"


class TMDBSearchResult(BaseModel):
    """A search result from TMDB (lightweight for grid display)."""

    id: int
    title: str
    overview: str
    poster_url: Optional[str]
    backdrop_url: Optional[str]
    media_type: MediaType
    release_year: Optional[str]
    vote_average: float = 0.0


def _parse_movie_search(movie: dict) -> TMDBSearchResult:
    """Parse a movie search result from TMDB."""
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")
    release_date = movie.get("release_date", "")

    return TMDBSearchResult(
        id=movie["id"],
        title=movie.get("title", "Unknown"),
        overview=movie.get("overview", ""),
        poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path
        else None,
        backdrop_url=f"https://image.tmdb.org/t/p/w780{backdrop_path}"
        if backdrop_path
        else None,
        media_type=MediaType.MOVIE,
        release_year=release_date[:4] if release_date else None,
        vote_average=movie.get("vote_average", 0.0),
    )


def _parse_series_search(series: dict) -> TMDBSearchResult:
    """Parse a TV series search result from TMDB."""
    poster_path = series.get("poster_path")
    backdrop_path = series.get("backdrop_path")
    first_air_date = series.get("first_air_date", "")

    return TMDBSearchResult(
        id=series["id"],
        title=series.get("name", "Unknown"),
        overview=series.get("overview", ""),
        poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path
        else None,
        backdrop_url=f"https://image.tmdb.org/t/p/w780{backdrop_path}"
        if backdrop_path
        else None,
        media_type=MediaType.SERIES,
        release_year=first_air_date[:4] if first_air_date else None,
        vote_average=series.get("vote_average", 0.0),
    )


def search_movies(query: str) -> List[TMDBSearchResult]:
    """Search TMDB for movies."""
    search = tmdb.Search()
    search.movie(query=query)
    return [_parse_movie_search(m) for m in search.results[:12]]


def search_series(query: str) -> List[TMDBSearchResult]:
    """Search TMDB for TV series."""
    search = tmdb.Search()
    search.tv(query=query)
    return [_parse_series_search(s) for s in search.results[:12]]


def search_all(query: str) -> List[TMDBSearchResult]:
    """Search TMDB for both movies and TV series."""
    search = tmdb.Search()
    search.multi(query=query)

    results = []
    for item in search.results[:12]:
        media_type = item.get("media_type")
        if media_type == "movie":
            results.append(_parse_movie_search(item))
        elif media_type == "tv":
            results.append(_parse_series_search(item))
        # Skip "person" results

    return results


def search_tmdb(
    query: str, media_type: MediaType = MediaType.ALL
) -> List[TMDBSearchResult]:
    """Search TMDB based on media type."""
    if media_type == MediaType.MOVIE:
        return search_movies(query)
    elif media_type == MediaType.SERIES:
        return search_series(query)
    else:
        return search_all(query)


@cache
def get_movie_details(tmdb_id: int) -> Movie:
    """Fetch full movie details from TMDB."""
    movie_api = tmdb.Movies(tmdb_id)
    info = movie_api.info()

    poster_path = info.get("poster_path")
    backdrop_path = info.get("backdrop_path")
    release_date = info.get("release_date", "")

    return Movie(
        id=info["id"],
        title=info.get("title", "Unknown"),
        overview=info.get("overview", ""),
        poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path
        else None,
        backdrop_url=f"https://image.tmdb.org/t/p/w780{backdrop_path}"
        if backdrop_path
        else None,
        release_date=release_date,
        release_year=release_date[:4] if release_date else None,
        vote_average=info.get("vote_average", 0.0),
        runtime=info.get("runtime"),
        genres=[g["name"] for g in info.get("genres", [])],
        imdb_id=info.get("imdb_id"),
    )


@cache
def get_series_details(tmdb_id: int) -> TVSeries:
    """Fetch full TV series details from TMDB including seasons and episodes."""
    tv_api = tmdb.TV(tmdb_id)
    info = tv_api.info()

    poster_path = info.get("poster_path")
    backdrop_path = info.get("backdrop_path")
    first_air_date = info.get("first_air_date", "")

    # Parse seasons (excluding specials - season 0) and fetch episodes for each
    seasons = []
    for s in info.get("seasons", []):
        if s.get("season_number", 0) > 0:
            # Fetch episodes for this season
            episodes = get_season_episodes(tmdb_id, s["season_number"])
            seasons.append(
                Season(
                    season_number=s["season_number"],
                    name=s.get("name", f"Season {s['season_number']}"),
                    episode_count=s.get("episode_count", 0),
                    air_date=s.get("air_date"),
                    overview=s.get("overview", ""),
                    episodes=episodes,
                )
            )

    return TVSeries(
        id=info["id"],
        title=info.get("name", "Unknown"),
        overview=info.get("overview", ""),
        poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}"
        if poster_path
        else None,
        backdrop_url=f"https://image.tmdb.org/t/p/w780{backdrop_path}"
        if backdrop_path
        else None,
        first_air_date=first_air_date,
        release_year=first_air_date[:4] if first_air_date else None,
        vote_average=info.get("vote_average", 0.0),
        number_of_seasons=info.get("number_of_seasons", 0),
        number_of_episodes=info.get("number_of_episodes", 0),
        seasons=seasons,
        genres=[g["name"] for g in info.get("genres", [])],
        status=info.get("status", ""),
    )


def get_season_episodes(tmdb_id: int, season_number: int) -> List[Episode]:
    """Fetch episodes for a specific season."""
    season_api = tmdb.TV_Seasons(tmdb_id, season_number)
    info = season_api.info()

    episodes = []
    for ep in info.get("episodes", []):
        episodes.append(
            Episode(
                episode_number=ep["episode_number"],
                name=ep.get("name", f"Episode {ep['episode_number']}"),
                overview=ep.get("overview", ""),
                air_date=ep.get("air_date"),
                runtime=ep.get("runtime"),
            )
        )

    return episodes
