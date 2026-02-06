"""API routes returning JSON for HTMX or external tools."""

from typing import List

from fastapi import APIRouter, Query

from app.providers import ProviderRegistry
from app.services.tmdb import search_tmdb, MediaType, TMDBSearchResult

router = APIRouter()


@router.get("/search", response_model=List[TMDBSearchResult])
async def api_search(
    q: str = Query(..., description="Search query"),
    media_type: str = Query("all", description="Media type: movie, tv, or all"),
):
    """Search TMDB for content.

    Returns JSON results for use by HTMX or external API consumers.
    """
    if media_type == "movie":
        mt = MediaType.MOVIE
    elif media_type == "tv":
        mt = MediaType.SERIES
    else:
        mt = MediaType.ALL

    return search_tmdb(q, mt)


@router.get("/providers")
async def list_providers():
    """List all registered providers."""
    return {"providers": ProviderRegistry.names()}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mirrarr"}
