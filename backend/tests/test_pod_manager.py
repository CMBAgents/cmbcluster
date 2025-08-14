import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.pod_manager import PodManager

@pytest.fixture
def mock_pod_manager():
    """Create a mock pod manager for testing"""
    with patch('backend.pod_manager.config'), \
         patch('backend.pod_manager.client'):
        pm = PodManager()
        pm.k8s_client = Mock()
        pm.apps_client = Mock()
        return pm

@pytest.mark.asyncio
async def test_user_has_active_pod_false(mock_pod_manager):
    """Test checking for non-existent user pod"""
    result = await mock_pod_manager.user_has_active_pod("non-existent-user")
    assert result is False

@pytest.mark.asyncio
async def test_generate_pod_name(mock_pod_manager):
    """Test pod name generation"""
    pod_name = mock_pod_manager._generate_pod_name("test-user-123")
    assert "user-test-user-123" in pod_name
    assert pod_name.startswith("user-")

def test_pod_manager_initialization(mock_pod_manager):
    """Test that pod manager initializes correctly"""
    assert mock_pod_manager is not None
    assert hasattr(mock_pod_manager, 'user_environments')
