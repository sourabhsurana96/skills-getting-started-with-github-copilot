import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


def make_activity_url(activity_name: str, path: str) -> str:
    # ensure activity name is URL-safe
    encoded = urllib.parse.quote(activity_name, safe='')
    return f"/activities/{encoded}/{path}"


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore activities to a fresh copy before each test"""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original


def test_get_activities():
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert isinstance(data["Soccer Team"]["participants"], list)


def test_signup_and_duplicate():
    activity = "Soccer Team"
    email = "tester@example.com"

    # signup should succeed
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    assert f"Signed up {email}" in res.json()["message"]

    # now the participant should be present
    res = client.get("/activities")
    assert email in res.json()[activity]["participants"]

    # signup again should fail with 400
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 400


def test_delete_participant():
    activity = "Soccer Team"
    email = "lucas@mergington.edu"  # existing participant

    # confirm participant exists
    res = client.get("/activities")
    assert email in res.json()[activity]["participants"]

    # delete participant
    res = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert res.status_code == 200
    assert f"Removed {email}" in res.json()["message"]

    # ensure participant removed
    res = client.get("/activities")
    assert email not in res.json()[activity]["participants"]


def test_delete_nonexistent_participant():
    activity = "Soccer Team"
    email = "not-in-list@example.com"

    res = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert res.status_code == 400


def test_activity_not_found():
    res = client.post("/activities/NoSuchClub/signup", params={"email": "a@b.com"})
    assert res.status_code == 404

    res = client.delete("/activities/NoSuchClub/participants", params={"email": "a@b.com"})
    assert res.status_code == 404
