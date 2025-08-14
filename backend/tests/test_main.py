import pytest
from fastapi.testclient import TestClient
import os

# Mock kubernetes before importing main
with pytest.MonkeyPatch().context() as m:
    m.setenv("DEV_MODE", "true")
    m.setenv("MOCK_KUBERNETES", "true")
    from backend.main import app

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

def test_stream_endpoint():
    """Test the /stream SSE endpoint."""
    headers = {"Authorization": "Bearer dev-token"}
    with client.stream("GET", "/stream", headers=headers) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # The TestClient's stream context manager allows iterating over chunks
        full_response_text = ""
        for chunk in response.iter_text():
            full_response_text += chunk

        expected_text = "This is a simulated stream of tokens from a large language model. " \
                        "Each word is sent as a separate chunk to demonstrate live updates " \
                        "on the client-side."

        # The content will be in the format "data: word \n\n"
        # We need to parse it and reconstruct the sentence.
        lines = full_response_text.strip().split('\n\n')
        decoded_words = [line.replace('data: ', '').strip() for line in lines]

        # Normalize spaces for comparison
        expected_words = expected_text.split()
        assert decoded_words == expected_words
