import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock kubernetes before importing main
with pytest.MonkeyPatch().context() as m:
    m.setenv("DEV_MODE", "true")
    m.setenv("MOCK_KUBERNETES", "true")
    from main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # Fix: Check for the actual key structure
    assert "service" in data
    assert "CMBCluster API" in data["service"]
    assert data["status"] == "healthy"
    assert "version" in data

def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_app_creation():
    """Test that the FastAPI app is created properly"""
    assert app is not None
    assert app.title == "CMBCluster API"
