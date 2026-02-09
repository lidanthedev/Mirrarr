"""UI routes returning HTML via Jinja2 templates."""

import logging
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

from app.services.tmdb import (
    search_tmdb,
    MediaType,
    get_series_details,
)
from app.services.search import (
    get_provider_results_for_movie,
    get_provider_results_for_episode,
    get_single_provider_results_for_movie,
    get_single_provider_results_for_episode,
    select_best_result,
)
from app.providers import ProviderRegistry
from app.services.download_manager import manager

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

    return templates.TemplateResponse(
        "partials/series_modal.html",
        {
            "request": request,
            "series": series,
            "seasons": series.seasons,
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
    """Return the provider selection modal with loading skeletons.

    Shows immediately with loading spinners for each provider,
    which then fetch their results independently via HTMX.
    """
    from app.services.tmdb import get_movie_details, get_series_details

    # Get media info for the header (fast TMDB lookup only)
    if media_type == "movie":
        media = get_movie_details(tmdb_id)
        if not title:
            title = media.title
        if not poster_url and media.poster_url:
            poster_url = media.poster_url
    else:
        media = get_series_details(tmdb_id)
        if not title:
            title = media.title
        if not poster_url and media.poster_url:
            poster_url = media.poster_url

    # Get list of all registered providers for loading skeletons
    provider_names = ProviderRegistry.names()

    return templates.TemplateResponse(
        "partials/provider_modal.html",
        {
            "request": request,
            "provider_names": provider_names,
            "title": title,
            "poster_url": poster_url,
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "season": season,
            "episode": episode,
            "media": media,
        },
    )


@router.get("/provider-results/{media_type}/{tmdb_id}/{provider_name}")
async def provider_result(
    request: Request,
    media_type: str,
    tmdb_id: int,
    provider_name: str,
    season: int = 1,
    episode: int = 1,
):
    """Fetch results from a single provider and return HTML partial.

    Called by HTMX on page load for each provider to enable incremental loading.
    """
    if media_type == "movie":
        _, results = await get_single_provider_results_for_movie(tmdb_id, provider_name)
    else:
        _, results = await get_single_provider_results_for_episode(
            tmdb_id, season, episode, provider_name
        )

    return templates.TemplateResponse(
        "partials/provider_result.html",
        {
            "request": request,
            "provider_name": provider_name,
            "provider_results": results,
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "season": season,
            "episode": episode,
        },
    )


@router.get("/auto-button/{media_type}/{tmdb_id}")
async def auto_button(
    request: Request,
    media_type: str,
    tmdb_id: int,
    season: int = 1,
    episode: int = 1,
):
    """Return the AUTO button after all providers have loaded.

    Waits for all providers to complete, then returns the best result button.
    """
    if media_type == "movie":
        _, results = await get_provider_results_for_movie(tmdb_id)
    else:
        _, results = await get_provider_results_for_episode(tmdb_id, season, episode)

    best_result = select_best_result(results)

    return templates.TemplateResponse(
        "partials/auto_button.html",
        {
            "request": request,
            "best_result": best_result,
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "season": season,
            "episode": episode,
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

    Finds the best quality result and queues it for download.
    """
    _, results = await get_provider_results_for_episode(tmdb_id, season, episode)
    best = select_best_result(results)

    if best:
        # Actually queue the download with provider-specific yt_opts
        filename = best.filename
        provider_name = best.provider_name
        provider = ProviderRegistry.get(provider_name)
        if provider is None:
            logging.warning(f"Provider '{provider_name}' not found in registry")
            return templates.TemplateResponse(
                "partials/toast.html",
                {
                    "request": request,
                    "message": f"Provider '{provider_name}' not found",
                    "type": "error",
                },
            )
        yt_opts = provider.get_yt_opts()
        download_id = await manager.add_download(
            best.download_url, client_opts=yt_opts, custom_filename=filename or None
        )
        print(
            f"[DOWNLOAD QUEUED] ID={download_id} {best.quality} from {best.source_site}: {best.download_url}"
        )

        display_name = filename if filename else best.quality

        return templates.TemplateResponse(
            "partials/auto_download.html",
            {
                "request": request,
                "download_url": best.download_url,
                "quality": best.quality,
                "source": best.source_site,
                "download_id": download_id,
                "filename": filename,
                "display_name": display_name,
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

    Finds the best quality result and queues it for download.
    """
    _, results = await get_provider_results_for_movie(tmdb_id)
    best = select_best_result(results)

    if best:
        # Actually queue the download with provider-specific yt_opts
        filename = best.filename
        provider_name = best.provider_name
        provider = ProviderRegistry.get(provider_name)
        if provider is None:
            logging.warning(f"Provider '{provider_name}' not found in registry")
            return templates.TemplateResponse(
                "partials/toast.html",
                {
                    "request": request,
                    "message": f"Provider '{provider_name}' not found",
                    "type": "error",
                },
            )
        download_id = await manager.add_download(
            best.download_url,
            custom_filename=filename or None,
            client_opts=provider.get_yt_opts(),
        )
        print(
            f"[DOWNLOAD QUEUED] ID={download_id} {best.quality} from {best.source_site}: {best.download_url}"
        )

        display_name = filename if filename else best.quality

        return templates.TemplateResponse(
            "partials/auto_download.html",
            {
                "request": request,
                "download_url": best.download_url,
                "quality": best.quality,
                "source": best.source_site,
                "download_id": download_id,
                "filename": filename,
                "display_name": display_name,
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
    filename: str = "",
):
    """Queue a download via yt_dlp download manager.

    Shows toast notification and actually queues the download.
    """
    provider = ProviderRegistry.get(source)
    if provider is None:
        logging.warning(f"Provider '{source}' not found in registry")
        return templates.TemplateResponse(
            "partials/toast.html",
            {
                "request": request,
                "message": f"Provider '{source}' not found",
                "type": "error",
            },
        )
    # Actually queue the download via the manager, with optional custom filename
    download_id = await manager.add_download(
        url, custom_filename=filename or None, client_opts=provider.get_yt_opts()
    )
    print(f"[DOWNLOAD QUEUED] ID={download_id} {quality} from {source}: {url}")

    # Use filename for display, fallback to quality
    display_name = filename if filename else quality

    return templates.TemplateResponse(
        "partials/auto_download.html",
        {
            "request": request,
            "download_url": url,
            "quality": quality,
            "source": source,
            "download_id": download_id,
            "filename": filename,
            "display_name": display_name,
        },
    )


@router.get("/downloads")
async def downloads_page(request: Request):
    """Render the downloads management page."""
    downloads = manager.get_all_downloads()
    return templates.TemplateResponse(
        "downloads.html",
        {
            "request": request,
            "downloads": downloads,
            "page_title": "Downloads",
        },
    )


@router.get("/downloads/list")
async def downloads_list_partial(request: Request):
    """Return the downloads list partial (for HTMX polling)."""
    downloads = manager.get_all_downloads()
    return templates.TemplateResponse(
        "partials/download_list.html",
        {
            "request": request,
            "downloads": downloads,
        },
    )
