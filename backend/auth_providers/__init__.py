"""
Authentication provider abstraction layer for CMBCluster.

This module provides a cloud-agnostic authentication interface that supports
multiple OAuth providers (Google OAuth, AWS Cognito, etc.).
"""

from .base import AuthProvider
from .factory import AuthProviderFactory

__all__ = [
    'AuthProvider',
    'AuthProviderFactory',
]
