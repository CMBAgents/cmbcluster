import pytest
from httpx import AsyncClient
from fastapi import status
import os

# Set env vars before importing the app
os.environ['DEV_MODE'] = 'true'
os.environ['MOCK_KUBERNETES'] = 'true'
os.environ['DATABASE_PATH'] = ':memory:'

from ..main import app
from ..auth import get_current_user

# Mock user for authenticated endpoints
async def override_get_current_user():
    return {"sub": "testuser", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/science/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
@pytest.mark.parametrize("data_type", [
    "Random Normal",
    "CMB Temperature Map",
    "Galaxy Survey",
    "Time Series",
])
async def test_generate_data(data_type: str):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/science/analysis/generate",
            json={"data_type": data_type, "n_points": 100}
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data_type"] == data_type
    assert "data" in data
    assert len(data["data"]) > 0

@pytest.mark.asyncio
async def test_generate_data_invalid_type():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/science/analysis/generate",
            json={"data_type": "Invalid Type", "n_points": 100}
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_basic_math():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/science/calculator/basic",
            json={"num1": 5, "operation": "+", "num2": 3}
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["result"] == 8

@pytest.mark.asyncio
async def test_array_operations():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/science/calculator/array",
            json={"size": 50}
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "statistics" in data
    assert "values_preview" in data
    assert len(data["values_preview"]) == 50

@pytest.mark.asyncio
async def test_get_power_spectrum():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/science/cosmology/power-spectrum")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["plot_type"] == "CMB Power Spectrum"
    assert "x_values" in data
    assert "y_values" in data

@pytest.mark.asyncio
async def test_get_correlation_function():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/science/cosmology/correlation-function")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["plot_type"] == "Galaxy Two-Point Correlation Function"
    assert "x_values" in data
    assert "y_values" in data

@pytest.mark.asyncio
async def test_notebook_execute_placeholder():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/science/notebook/execute",
            json={"code": "print('hello')"}
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "placeholder"
    assert "This endpoint is a placeholder" in data["message"]
