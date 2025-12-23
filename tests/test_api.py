"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def client():
    """Create test client"""
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test /health endpoint returns OK"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestChatEndpoint:
    """Test chat endpoint functionality"""
    
    @patch('main.run_agent')
    def test_chat_success(self, mock_run_agent, client):
        """Test successful chat request"""
        # Mock the agent response
        mock_run_agent.return_value = {
            "text": "Here are the top 10 media sources",
            "data": [{"media_source": "facebook", "clicks": 15000}]
        }
        
        response = client.post(
            "/chat",
            json={"message": "Show me top media sources"}
        )
        
        assert response.status_code == 200
        # Add more assertions based on expected response
    
    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        response = client.post(
            "/chat",
            json={"message": ""}
        )
        
        # Should handle empty message gracefully
        assert response.status_code in [200, 400]
    
    def test_chat_invalid_json(self, client):
        """Test chat with invalid JSON"""
        response = client.post(
            "/chat",
            data="invalid json"
        )
        
        assert response.status_code == 422  # Validation error


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are set correctly"""
        response = client.options(
            "/chat",
            headers={"Origin": "http://localhost:5173"}
        )
        
        # CORS should allow the frontend origin
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
