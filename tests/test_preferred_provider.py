import pytest
from unittest.mock import patch, MagicMock
from app.services.search import select_best_result
from app.providers.base import MovieResult

def test_select_best_result_quality_priority():
    """Test that higher quality is preferred when no preferred provider is set."""
    results = [
        MovieResult(title="M1", quality="720p", size=1000, download_url="url1", source_site="S1", provider_name="P1"),
        MovieResult(title="M2", quality="1080p", size=2000, download_url="url2", source_site="S2", provider_name="P2"),
        MovieResult(title="M3", quality="480p", size=500, download_url="url3", source_site="S3", provider_name="P3"),
    ]
    
    with patch("app.services.search.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(preferred_provider=None, quality_limit="2160p")
        best = select_best_result(results)
        assert best.quality == "1080p"

def test_select_best_result_preferred_provider():
    """Test that preferred provider is prioritized over higher quality."""
    results = [
        MovieResult(title="M1", quality="1080p", size=2000, download_url="url1", source_site="S1", provider_name="P1"),
        MovieResult(title="M2", quality="720p", size=1000, download_url="url2", source_site="S2", provider_name="P2"),
    ]
    
    with patch("app.services.search.get_settings") as mock_settings:
        # P2 is preferred even if it's 720p and P1 is 1080p
        mock_settings.return_value = MagicMock(preferred_provider="P2", quality_limit="2160p")
        best = select_best_result(results)
        assert best.provider_name == "P2"
        assert best.quality == "720p"

def test_select_best_result_quality_limit():
    """Test that quality limit is strictly respected (higher quality results are ignored)."""
    results = [
        MovieResult(title="M1", quality="2160p", size=5000, download_url="url1", source_site="S1", provider_name="P1"),
        MovieResult(title="M2", quality="1080p", size=2000, download_url="url2", source_site="S2", provider_name="P2"),
    ]
    
    with patch("app.services.search.get_settings") as mock_settings:
        # Limit to 1080p, so 2160p should be filtered out entirely.
        mock_settings.return_value = MagicMock(preferred_provider=None, quality_limit="1080p")
        best = select_best_result(results)
        # Only M2 (1080p) should be in the list after filtering.
        assert best.quality == "1080p"
        assert best.title == "M2"

def test_select_best_result_all_exceed_limit():
    """Test that None is returned if all results exceed the quality limit."""
    results = [
        MovieResult(title="M1", quality="2160p", size=5000, download_url="url1", source_site="S1", provider_name="P1"),
    ]
    
    with patch("app.services.search.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(preferred_provider=None, quality_limit="1080p")
        best = select_best_result(results)
        assert best is None

# Note: select_best_result uses a negative size tie-breaker to prefer smaller files.
# This logic should be kept in sync with findBestFromResults in provider_modal.html
# which also uses a subtraction (score = ... - r.sizeMb) for the same effect.
def test_select_best_result_size_fallback():
    """Test that smaller size is preferred for same quality."""
    results = [
        MovieResult(title="M1", quality="1080p", size=3000, download_url="url1", source_site="S1", provider_name="P1"),
        MovieResult(title="M2", quality="1080p", size=2000, download_url="url2", source_site="S2", provider_name="P2"),
    ]
    
    with patch("app.services.search.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(preferred_provider=None, quality_limit="2160p")
        best = select_best_result(results)
        assert best.size == 2000
