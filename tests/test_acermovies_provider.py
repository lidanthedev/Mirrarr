import pytest
from unittest.mock import patch, AsyncMock
from app.providers.acermovies_provider import AcerMoviesProvider
from app.models.media import Movie, TVSeries


@pytest.mark.asyncio
async def test_acermovies_provider_name():
    """Test provider name."""
    provider = AcerMoviesProvider()
    assert provider.name == "AcerMovies"


@pytest.mark.asyncio
async def test_acermovies_get_movie():
    """Test fetching movie links with mocked response."""
    provider = AcerMoviesProvider()
    movie = Movie(id=293660, title="Deadpool", release_year="2016")

    # Mock responses
    mock_search_data = {
        "searchResult": [
            {
                "title": "Deadpool (2016) 720p",
                "url": "http://mock/movie",
                "year": "2016",
            }
        ]
    }
    mock_qualities_data = {
        "sourceQualityList": [{"quality": "720p", "url": "http://mock/quality"}]
    }
    mock_source_url_data = {"sourceUrl": "http://final/pool.mp4"}

    with patch.object(provider, "_post", new_callable=AsyncMock) as mock_post:
        # Define side effects based on args
        async def side_effect(endpoint, _payload):
            if endpoint == "search":
                return mock_search_data
            elif endpoint == "sourceQuality":
                return mock_qualities_data
            elif endpoint == "sourceUrl":
                return mock_source_url_data
            return {}

        mock_post.side_effect = side_effect

        results = await provider.get_movie(movie)

        assert len(results) == 1
        res = results[0]
        assert res.title == movie.title
        assert res.download_url == "http://final/pool.mp4"
        assert res.provider_name == "AcerMovies"
        assert res.quality == "720p"


@pytest.mark.asyncio
async def test_acermovies_get_series_episode():
    """Test fetching series episode links with mocked response."""
    provider = AcerMoviesProvider()
    series = TVSeries(
        id=1396, title="Breaking Bad", release_year="2008", number_of_seasons=5
    )
    season = 1
    episode = 1

    # Mock data
    mock_search_data = {
        "searchResult": [
            {
                "title": "Breaking Bad (Season 1-5)",
                "url": "http://mock/show",
            }
        ]
    }
    # Level 1: List of Seasons/Segments
    mock_episodes_level_1 = {
        "sourceEpisodes": [
            {"title": "Season 1", "link": "http://mock/s1"},  # Index 0
            {"title": "Season 2", "link": "http://mock/s2"},
            # ...
        ]
    }
    # Level 2: Episodes in Season 1
    mock_episodes_level_2 = {
        "sourceEpisodes": [
            {"title": "Episode 1", "link": "http://mock/s1e1"},
            {"title": "Episode 2", "link": "http://mock/s1e2"},
        ]
    }

    mock_source_url_data = {"sourceUrl": "http://final/bb_s1e1.mp4"}

    with patch.object(provider, "_post", new_callable=AsyncMock) as mock_post:

        async def side_effect(endpoint, _payload):
            if endpoint == "search":
                return mock_search_data
            elif endpoint == "sourceEpisodes":
                p_url = _payload.get("url")
                if p_url == "http://mock/show":
                    return mock_episodes_level_1
                elif p_url == "http://mock/s1":
                    return mock_episodes_level_2
                return {}
            elif endpoint == "sourceUrl":
                return mock_source_url_data
            return {}

        mock_post.side_effect = side_effect

        results = await provider.get_series_episode(series, season, episode)

        assert len(results) == 1
        res = results[0]
        assert "Breaking Bad" in res.title
        assert res.season == season
        assert res.episode == episode
        assert res.download_url == "http://final/bb_s1e1.mp4"


@pytest.mark.asyncio
async def test_acermovies_search_no_results():
    """Test search with no results."""
    provider = AcerMoviesProvider()
    movie = Movie(id=0, title="NonExistent", release_year="2099")

    with patch.object(provider, "_post", new_callable=AsyncMock) as mock_post:

        async def side_effect(endpoint, _payload):
            if endpoint == "search":
                return {"searchResult": []}
            return {}

        mock_post.side_effect = side_effect

        results = await provider.get_movie(movie)
        assert len(results) == 0
