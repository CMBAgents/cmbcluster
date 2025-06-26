import pytest
from config import Settings

def test_settings_creation():
    """Test that settings can be created"""
    settings = Settings()
    assert settings is not None

def test_default_values():
    """Test default configuration values"""
    settings = Settings()
    assert settings.namespace == "cmbcluster"
    assert settings.max_user_pods == 1
    assert settings.jwt_algorithm == "HS256"

def test_development_mode():
    """Test development mode settings"""
    settings = Settings(dev_mode=True)
    assert settings.dev_mode is True
