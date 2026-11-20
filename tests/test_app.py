import src.app as app_module
import pytest
from fastapi.testclient import TestClient


ACTIVITY_NAME = "Test Activity"
REGISTERED_EMAIL = "registered@mergington.edu"


@pytest.fixture
def isolated_activities(monkeypatch):
    activities = {
        ACTIVITY_NAME: {
            "description": "A test activity",
            "schedule": "Mondays, 3:00 PM",
            "max_participants": 10,
            "participants": [REGISTERED_EMAIL],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(isolated_activities):
    return TestClient(app_module.app)


def test_root_redirects_to_web_app(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, isolated_activities):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == isolated_activities


def test_signup_adds_participant(client, isolated_activities):
    # Arrange
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert isolated_activities[ACTIVITY_NAME]["participants"] == [
        REGISTERED_EMAIL,
        email,
    ]


def test_signup_rejects_duplicate_participant(client, isolated_activities):
    # Arrange

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": REGISTERED_EMAIL},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert isolated_activities[ACTIVITY_NAME]["participants"] == [REGISTERED_EMAIL]


def test_signup_rejects_unknown_activity(client, isolated_activities):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": "new-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert list(isolated_activities) == [ACTIVITY_NAME]


def test_unregister_removes_participant(client, isolated_activities):
    # Arrange
    email = "leaving-student@mergington.edu"
    other_email = "staying-student@mergington.edu"
    isolated_activities[ACTIVITY_NAME]["participants"].extend([email, email, other_email])

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert isolated_activities[ACTIVITY_NAME]["participants"] == [
        REGISTERED_EMAIL,
        other_email,
    ]


def test_unregister_rejects_unregistered_participant(client, isolated_activities):
    # Arrange
    email = "unknown-student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert isolated_activities[ACTIVITY_NAME]["participants"] == [REGISTERED_EMAIL]


def test_unregister_rejects_unknown_activity(client, isolated_activities):
    # Arrange
    unknown_activity = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{unknown_activity}/signup",
        params={"email": REGISTERED_EMAIL},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert list(isolated_activities) == [ACTIVITY_NAME]
