"""
Pytest configuration and fixtures for testing
"""
import pytest
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

@pytest.fixture
def sample_user_query():
    """Sample user query for testing"""
    return "Show me top 10 media sources by clicks yesterday"

@pytest.fixture
def sample_intent_analysis():
    """Sample intent analysis result"""
    return {
        "status": "ok",
        "intent": "data_query",
        "entities": {
            "metric": "clicks",
            "date_range": "yesterday",
            "limit": 10
        }
    }

@pytest.fixture
def mock_bq_results():
    """Mock BigQuery results"""
    return [
        {"media_source": "facebook", "clicks": 15000},
        {"media_source": "google", "clicks": 12000},
        {"media_source": "twitter", "clicks": 8500}
    ]
