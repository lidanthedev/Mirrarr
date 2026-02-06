"""UI routes returning HTML via Jinja2 templates."""

from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

from app.services.tmdb import (
    search_tmdb,
    MediaType,
    get_series_details,
    get_season_episodes,
)
from app.services.search import (
    get_provider_results_for_movie,
    get_provider_results_for_episode,
    select_best_result,
)

router = APIRouter()

# Templates directory
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/")
async def dashboard(request: Request):
    """Render the main dashboard page (search all)."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "media_type": "all", "page_title": "Search for Content"},
    )


@router.get("/movies")
async def movies_page(request: Request):
    """Render the movies search page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "media_type": "movie", "page_title": "Search Movies"},
    )


@router.get("/tv")
async def tv_page(request: Request):
    """Render the TV shows search page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "media_type": "tv", "page_title": "Search TV Shows"},
    )


@router.post("/search")
async def search(
    request: Request,
    query: str = Form(...),
    media_type: str = Form("all"),
):
    """Handle search form submission and return HTML partial."""
    if media_type == "movie":
        mt = MediaType.MOVIE
    elif media_type in ("tv", "series"):
        mt = MediaType.SERIES
    else:
        mt = MediaType.ALL

    results = search_tmdb(query, mt)

    return templates.TemplateResponse(
        "partials/search_results.html",
        {"request": request, "results": results, "query": query},
    )


@router.get("/series/{tmdb_id}")
async def series_modal(
    request: Request,
    tmdb_id: int,
):
    """Return the TV series modal with all seasons and episodes."""
    series = get_series_details(tmdb_id)

    # Fetch episodes for each season
    seasons_with_episodes = []
    for season in series.seasons:
        episodes = get_season_episodes(tmdb_id, season.season_number)
        season.episodes = episodes
        seasons_with_episodes.append(season)

    return templates.TemplateResponse(
        "partials/series_modal.html",
        {
            "request": request,
            "series": series,
            "seasons": seasons_with_episodes,
        },
    )


@router.get("/providers/{media_type}/{tmdb_id}")
async def provider_modal(
    request: Request,
    media_type: str,
    tmdb_id: int,
    title: str = "",
    poster_url: str = "",
    season: int = 1,
    episode: int = 1,
):
    """Return the provider selection modal for a movie/episode."""
    if media_type == "movie":
        media, results = await get_provider_results_for_movie(tmdb_id)
        if not title:
            title = media.title
        if not poster_url and media.poster_url:
            poster_url = media.poster_url
    else:
        media, results = await get_provider_results_for_episode(
            tmdb_id, season, episode
        )
        if not title:
            title = media.title
        if not poster_url and media.poster_url:
            poster_url = media.poster_url

    # Group results by provider
    results_by_provider = defaultdict(list)
    for result in results:
        results_by_provider[result.source_site].append(result)

    best_result = select_best_result(results)

    return templates.TemplateResponse(
        "partials/provider_modal.html",
        {
            "request": request,
            "results": results,
            "results_by_provider": dict(results_by_provider),
            "best_result": best_result,
            "title": title,
            "poster_url": poster_url,
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "season": season,
            "episode": episode,
            "media": media,
        },
    )


@router.get("/episode/auto/{tmdb_id}/{season}/{episode}")
async def episode_auto(
    request: Request,
    tmdb_id: int,
    season: int,
    episode: int,
):
    """Auto-download best quality for an episode.

    Shows a toast and logs the URL to console (simulated download).
    """
    _, results = await get_provider_results_for_episode(tmdb_id, season, episode)
    best = select_best_result(results)

    if best:
        return templates.TemplateResponse(
            "partials/auto_download.html",
            {
                "request": request,
                "download_url": best.download_url,
                "quality": best.quality,
                "source": best.source_site,
            },
        )

    return templates.TemplateResponse(
        "partials/toast.html",
        {"request": request, "message": "No downloads available", "type": "error"},
    )


@router.get("/movie/auto/{tmdb_id}")
async def movie_auto(
    request: Request,
    tmdb_id: int,
):
    """Auto-download best quality for a movie.

    Shows a toast and logs the URL to console (simulated download).
    """
    _, results = await get_provider_results_for_movie(tmdb_id)
    best = select_best_result(results)

    if best:
        return templates.TemplateResponse(
            "partials/auto_download.html",
            {
                "request": request,
                "download_url": best.download_url,
                "quality": best.quality,
                "source": best.source_site,
            },
        )

    return templates.TemplateResponse(
        "partials/toast.html",
        {"request": request, "message": "No downloads available", "type": "error"},
    )


@router.get("/download/queue")
async def download_queue(
    request: Request,
    url: str,
    quality: str = "",
    source: str = "",
    media_type: str = "movie",
    tmdb_id: int = 0,
    season: int = 1,
    episode: int = 1,
):
    """Queue a download - shows toast and logs URL to console.

    This is a simulated download - in production this would actually queue the download.
    """
    # Log the download (this is where actual download logic would go)
    print(f"[DOWNLOAD QUEUED] {quality} from {source}: {url}")

    return templates.TemplateResponse(
        "partials/auto_download.html",
        {
            "request": request,
            "download_url": url,
            "quality": quality,
            "source": source,
        },
    )
