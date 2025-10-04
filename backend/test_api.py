"""
Quick test script for FastAPI backend
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    print("SUCCESS: Root endpoint working")


def test_health():
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("SUCCESS: Health check working")


def test_list_images():
    """Test image listing."""
    response = client.get("/api/images")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "images" in data
    print(f"SUCCESS: Image listing working - found {data['total']} images")


def test_get_image():
    """Test get single image."""
    response = client.get("/api/images/1")
    if response.status_code == 200:
        data = response.json()
        assert "filename" in data
        print(f"SUCCESS: Get image working - {data['filename']}")
    else:
        print("WARNING: No images found (this is OK if data/raw is empty)")


def test_annotations():
    """Test annotation endpoints."""
    response = client.get("/api/annotations")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    print(f"SUCCESS: Annotation listing working - found {data['total']} annotations")


def test_review_queue():
    """Test review queue."""
    response = client.get("/api/review/queue")
    assert response.status_code == 200
    data = response.json()
    assert "total_pending" in data
    print(f"SUCCESS: Review queue working - {data['total_pending']} pending")


def test_review_statistics():
    """Test review statistics."""
    response = client.get("/api/review/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_images" in data
    print(f"SUCCESS: Review statistics working - {data['total_images']} total images")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing FastAPI Backend - Phase 2.5")
    print("=" * 60)
    print()

    try:
        test_root()
        test_health()
        test_list_images()
        test_get_image()
        test_annotations()
        test_review_queue()
        test_review_statistics()

        print()
        print("=" * 60)
        print("SUCCESS: ALL TESTS PASSED - Backend is working!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Start the server: python -m app.main")
        print("2. Open API docs: http://localhost:8000/docs")
        print("3. Build frontend to connect to this API")

    except AssertionError as e:
        print(f"FAILED: Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
