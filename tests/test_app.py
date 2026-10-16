import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_activity(monkeypatch):
    activity = {
        "description": "A test activity",
        "schedule": "Mondays, 3:00 PM - 4:00 PM",
        "max_participants": 5,
        "participants": ["existing@example.com"],
    }
    monkeypatch.setitem(activities, "Test Activity", activity)
    return activity


def test_root_redirects_to_frontend(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_includes_registered_activity(client, test_activity):
    # Arrange
    expected_activity = test_activity

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Test Activity"] == expected_activity


def test_signup_adds_participant(client, test_activity):
    # Arrange
    email = "new-participant@example.com"

    # Act
    response = client.post(
        "/activities/Test%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Test Activity"
    assert email in test_activity["participants"]


def test_signup_rejects_duplicate_participant(client, test_activity):
    # Arrange
    email = test_activity["participants"][0]

    # Act
    response = client.post(
        "/activities/Test%20Activity/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert test_activity["participants"] == [email]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Activity/signup"
    email = "student@example.com"

    # Act
    response = client.post(
        path,
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_unregisters_student(client, test_activity):
    # Arrange
    email = test_activity["participants"][0]

    # Act
    response = client.delete(
        "/activities/Test%20Activity/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Test Activity"
    assert email not in test_activity["participants"]


def test_remove_participant_rejects_missing_signup(client, test_activity):
    # Arrange
    email = "not-signed-up@example.com"

    # Act
    response = client.delete(
        "/activities/Test%20Activity/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown%20Activity/participants"
    email = "student@example.com"

    # Act
    response = client.delete(
        path,
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"