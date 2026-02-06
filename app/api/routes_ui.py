"""UI routes returning HTML via Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

from app.services.tmdb import search_tmdb, MediaType
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
    """Handle search form submission and return HTML partial.

    This endpoint is called by HTMX and returns only the
    search_results.html partial, not the full page.
    """
    # Convert string to MediaType enum
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
    """Return the provider selection modal for a movie/series."""
    if media_type == "movie":
        media, results = await get_provider_results_for_movie(tmdb_id)
        # Use fetched title/poster if not provided
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

    best_result = select_best_result(results)

    return templates.TemplateResponse(
        "partials/provider_modal.html",
        {
            "request": request,
            "results": results,
            "best_result": best_result,
            "title": title,
            "poster_url": poster_url,
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "media": media,
        },
    )
