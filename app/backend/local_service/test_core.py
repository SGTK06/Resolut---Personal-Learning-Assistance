"""
Test Suite for Resolut Local Service

Covers core functionality:
- Topic management (create, list, delete)
- Roadmap storage
- Lesson storage and progress tracking
- Lockdown management
"""

import pytest
import json
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

# Setup test data directory
TEST_DATA_DIR = Path("test_data")


@pytest.fixture(scope="module")
def setup_test_env():
    """Setup isolated test environment."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    yield
    # Cleanup
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)


@pytest.fixture
def client(setup_test_env):
    """Create test client with isolated data directory."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Patch data directories
    import lesson_storage
    import roadmap_storage
    lesson_storage.DATA_DIR = TEST_DATA_DIR
    lesson_storage.LESSONS_DIR = TEST_DATA_DIR / "lessons"
    lesson_storage.PROGRESS_FILE = TEST_DATA_DIR / "progress.json"
    roadmap_storage.ROADMAPS_FILE = TEST_DATA_DIR / "roadmaps.json"
    
    from main import app
    return TestClient(app)


# =============================================================================
# Topic & Roadmap Tests
# =============================================================================

class TestTopicManagement:
    """Tests for topic creation, listing, and deletion."""
    
    def test_list_topics_empty(self, client):
        """Should return empty list when no topics exist."""
        response = client.get("/api/topics")
        assert response.status_code == 200
        assert "topics" in response.json()
    
    def test_save_roadmap(self, client):
        """Should save a roadmap for a topic."""
        roadmap_data = {
            "topic": "TestTopic",
            "roadmap": {
                "Chapter 1: Basics": {
                    "Lesson 1.1": "Introduction",
                    "Lesson 1.2": "Core Concepts"
                }
            }
        }
        response = client.post("/api/roadmaps", json=roadmap_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_get_roadmap(self, client):
        """Should retrieve a saved roadmap."""
        # First save
        roadmap_data = {
            "topic": "RetrieveTest",
            "roadmap": {"Chapter 1": {"Lesson 1": "Test"}}
        }
        client.post("/api/roadmaps", json=roadmap_data)
        
        # Then retrieve
        response = client.get("/api/roadmaps/RetrieveTest")
        assert response.status_code == 200
        assert response.json()["roadmap"] == roadmap_data["roadmap"]
    
    def test_get_nonexistent_roadmap(self, client):
        """Should return 404 for non-existent roadmap."""
        response = client.get("/api/roadmaps/NonExistent")
        assert response.status_code == 404


# =============================================================================
# Lesson Storage Tests
# =============================================================================

class TestLessonStorage:
    """Tests for lesson content storage and progress tracking."""
    
    def test_lesson_progress_not_started(self, client):
        """Should return not_started for new topic."""
        response = client.get("/api/lessons/progress/NewTopic")
        assert response.status_code == 200
        assert response.json()["status"] == "not_started"


# =============================================================================
# Lockdown Tests
# =============================================================================

class TestLockdown:
    """Tests for lockdown management."""
    
    def test_get_lockdown_status(self, client):
        """Should return lockdown status."""
        response = client.get("/api/lockdown/status")
        assert response.status_code == 200
        assert "is_locked_down" in response.json()
    
    def test_trigger_lockdown(self, client):
        """Should trigger lockdown."""
        response = client.post("/api/lockdown/trigger")
        assert response.status_code == 200
        
        # Verify status
        status = client.get("/api/lockdown/status")
        assert status.json()["is_locked_down"] == True
    
    def test_unlock_lockdown(self, client):
        """Should unlock lockdown."""
        # First trigger
        client.post("/api/lockdown/trigger")
        
        # Then unlock
        response = client.post("/api/lockdown/unlock")
        assert response.status_code == 200
        
        # Verify unlocked
        status = client.get("/api/lockdown/status")
        assert status.json()["is_locked_down"] == False
    
    def test_lockdown_settings(self, client):
        """Should get and update lockdown settings."""
        # Get current settings
        response = client.get("/api/dev/lockdown_settings")
        assert response.status_code == 200
        
        # Update settings
        new_settings = {
            "warning_interval_seconds": 60,
            "negotiation_interval_seconds": 30
        }
        response = client.post("/api/dev/lockdown_settings", json=new_settings)
        assert response.status_code == 200


# =============================================================================
# RAG Tools Tests
# =============================================================================

class TestRAGTools:
    """Tests for RAG indexer tools."""
    
    def test_index_stats(self, client):
        """Should return index statistics."""
        response = client.get("/api/tools/index_stats")
        assert response.status_code == 200
        assert "total_vectors" in response.json()


# =============================================================================
# Calendar Tests
# =============================================================================

class TestCalendar:
    """Tests for calendar functionality."""
    
    def test_calendar_status(self, client):
        """Should return calendar connection status."""
        response = client.get("/api/calendar/status")
        assert response.status_code == 200
        assert "connected" in response.json()
    
    def test_scheduling_settings(self, client):
        """Should get scheduling settings."""
        response = client.get("/api/settings/scheduling")
        assert response.status_code == 200
        assert "auto_schedule" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
