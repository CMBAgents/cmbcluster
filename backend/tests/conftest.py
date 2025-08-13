import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def mock_gcp_storage(monkeypatch):
    """Mock the Google Cloud Storage client to avoid authentication errors during tests."""

    class MockStorageClient:
        def __init__(self, project=None):
            pass
        def bucket(self, name):
            return MockBucket(name)

    class MockBucket:
        def __init__(self, name):
            self.name = name
        def blob(self, blob_name):
            return MockBlob(blob_name)
        def list_blobs(self, prefix=None):
            return []

    class MockBlob:
        def __init__(self, name):
            self.name = name
            self._content = b""

        def upload_from_string(self, content):
            self._content = content.encode('utf-8')

        def download_as_bytes(self):
            return self._content

        def delete(self):
            pass

    monkeypatch.setattr("google.cloud.storage.Client", MockStorageClient)
