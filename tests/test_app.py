"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_store


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore every activity's participants list to its original state after each test."""
    original = {name: list(data["participants"]) for name, data in activities_store.items()}
    yield
    for name, data in activities_store.items():
        data["participants"] = original[name]


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        for activity in response.json().values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Underwater Basket Weaving/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Underwater Basket Weaving/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_non_participant_returns_404(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "nobody@mergington.edu"},
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()
