import pytest
from unittest.mock import Mock, patch
from backend.auth import create_access_token, verify_token
from backend.config import settings

def test_create_access_token():
    """Test JWT token creation"""
    user_data = {
        "id": "test-user-123",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Mock user object
    mock_user = Mock()
    mock_user.id = user_data["id"]
    mock_user.email = user_data["email"]
    mock_user.name = user_data["name"]
    mock_user.role.value = "user"
    
    token = create_access_token(mock_user)
    assert token is not None
    assert isinstance(token, str)

def test_verify_token_invalid():
    """Test token verification with invalid token"""
    with pytest.raises(Exception):  # Should raise HTTPException
        verify_token("invalid-token")

@patch('backend.auth.settings')
def test_dev_mode_bypass(mock_settings):
    """Test development mode authentication bypass"""
    mock_settings.dev_mode = True
    # Add your dev mode tests here
    assert True  # Placeholder
