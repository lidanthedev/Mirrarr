from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.tmdb import TMDBSearchResult, MediaType

client = TestClient(app)

# Mock data
mock_results = [
    TMDBSearchResult(
        id=1,
        title="Test Movie",
        overview="Test Overview",
        poster_url=None,
        backdrop_url=None,
        media_type=MediaType.MOVIE,
        release_year="2023",
        vote_average=8.0,
    )
]


@patch(
    "app.api.routes_api.search_tmdb", side_effect=AsyncMock(return_value=mock_results)
)
def test_api_search_async_fix(mock_search):
    """
    Test that api_search awaits the async search_tmdb function.
    If it fails to await, it returns a coroutine, which causes FastAPI to error
    (likely 500 or validation error) because it doesn't match List[TMDBSearchResult].
    """
    # Force use of a specific backend to ensure the mock is used
    response = client.get("/api/search?q=test&media_type=movie")

    # If the bug exists (missing await), this will likely fail with 500 or validation error
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test Movie"


@patch(
    "app.api.routes_ui.search_tmdb", side_effect=AsyncMock(return_value=mock_results)
)
def test_ui_search_async_success(mock_search):
    """
    Test that the UI search route works correctly (it was already correct).
    """
    response = client.post("/search", data={"query": "test", "media_type": "movie"})

    assert response.status_code == 200
    assert "Test Movie" in response.text
