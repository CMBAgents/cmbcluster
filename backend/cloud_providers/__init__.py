"""
Cloud Provider Abstraction Layer

This package provides a unified interface for interacting with different cloud providers (GCP, AWS, etc.).
The abstraction allows CMBCluster to be deployed on multiple cloud platforms while maintaining
a consistent application layer.
"""

from .base import CloudStorageProvider
from .factory import StorageProviderFactory

__all__ = [
    "CloudStorageProvider",
    "StorageProviderFactory",
]
