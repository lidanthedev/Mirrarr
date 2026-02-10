"""API routes returning JSON for HTMX or external tools."""

from typing import Any, List
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.providers import ProviderRegistry
from app.services.download_manager import manager
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

    return await search_tmdb(q, mt)


@router.get("/providers")
async def list_providers():
    """List all registered providers."""
    return {"providers": ProviderRegistry.names()}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mirrarr"}


# --- Download Management ---


class DownloadRequest(BaseModel):
    """Request body for queueing a download."""

    url: str
    opts: dict[str, Any] | None = None


@router.post("/downloads")
async def queue_download(request: DownloadRequest):
    """Queue a new download."""

    parsed = urlparse(request.url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400, detail="Invalid URL scheme. Only http/https are allowed."
        )

    download_id = await manager.add_download(request.url, request.opts)
    return {"id": download_id, "status": "queued"}


@router.get("/downloads")
async def list_downloads():
    """List all downloads and their statuses."""
    return {"downloads": manager.get_all_downloads()}


@router.get("/downloads/{download_id}")
async def get_download(download_id: str):
    """Get a specific download status."""
    status = manager.get_download(download_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Download not found")
    return status
