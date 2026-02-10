import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from app.providers.rivestream_provider import RiveStreamProvider
from app.models.media import TVSeries
from app.services.tmdb import TMDBError, _get_movie_details_sync, movie_cache
import logging

# Configure logging to capture output
logging.basicConfig(level=logging.INFO)


class TestRefactors(unittest.TestCase):
    def test_rivestream_malformed_data(self):
        """Test Rivestream provider validation logic."""
        provider = RiveStreamProvider()
        # Mock solve to avoid computation
        provider.rive_solver.solve = MagicMock(return_value="test_key")

        series = TVSeries(
            id=123,
            title="Test Show",
            overview="",
            first_air_date="",
            release_year="2023",
            vote_average=0.0,
            number_of_seasons=1,
            number_of_episodes=10,
            seasons=[],
            genres=[],
            status="",
        )

        # Mock niquests response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "sources": [
                    {
                        "url": "http://valid.com",
                        "quality": "1080",
                        "format": "mp4",
                        "size": 100,
                    },  # Valid
                    {"url": "http://noquality.com", "format": "mp4"},  # Missing quality
                    {
                        "quality": "1080",
                        "format": "mp4",
                    },  # Missing url (now checked with .get)
                    {"url": "http://noformat.com", "quality": "1080"},  # Missing format
                    {
                        "url": "http://nosize.com",
                        "quality": "720",
                        "format": "mkv",
                    },  # Missing size (optional)
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        # Use AsyncMock for aget
        with patch(
            "app.providers.rivestream_provider.niquests.aget", new_callable=AsyncMock
        ) as mock_aget:
            mock_aget.return_value = mock_response

            # We need to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                provider.get_series_episode_with_service(series, 1, 1, "server1")
            )
            loop.close()

            # Expect 2 results: the fully valid one and the one missing size (which is optional)
            self.assertEqual(len(results), 2, "Should have 2 valid results")
            self.assertEqual(results[0].download_url, "http://valid.com")
            self.assertEqual(results[1].download_url, "http://nosize.com")
            self.assertEqual(results[1].size, 0, "Default size should be 0")

    def test_tmdb_exception_chaining(self):
        """Test that TMDBError preserves the original exception."""
        # Clear cache to ensure we hit the function
        movie_cache.clear()

        with patch("app.services.tmdb.tmdb.Movies") as MockMovies:
            mock_instance = MockMovies.return_value
            original_exc = ValueError("Simulated API Error")
            mock_instance.info.side_effect = original_exc

            try:
                _get_movie_details_sync(999)
            except TMDBError as e:
                self.assertIsInstance(e, TMDBError)
                self.assertEqual(
                    e.__cause__,
                    original_exc,
                    "Exception should be chained with 'from exc'",
                )
            except Exception as e:
                self.fail(f"Raised unexpected exception type: {type(e)}")
            else:
                self.fail("Should have raised TMDBError")


if __name__ == "__main__":
    unittest.main()
