from fastapi.testclient import TestClient

from main import app
from services.band_playbook import Band, list_playbooks

client = TestClient(app)


def test_list_bands():
    response = client.get("/api/v1/teacher/bands")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 4
    assert [band["code"] for band in body["bands"]] == [
        playbook.code.value for playbook in list_playbooks()
    ]


def test_get_band_by_code():
    response = client.get("/api/v1/teacher/bands/be")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == Band.BE.value
    assert body["question_count"] == 4
    assert body["regrouping"] is False


def test_get_band_by_full_name():
    response = client.get("/api/v1/teacher/bands/Exceeding%20Expectation")

    assert response.status_code == 200
    assert response.json()["code"] == Band.EE.value


def test_get_band_by_slug():
    response = client.get("/api/v1/teacher/bands/meeting-expectation")

    assert response.status_code == 200
    assert response.json()["code"] == Band.ME.value


def test_unknown_band_returns_404():
    response = client.get("/api/v1/teacher/bands/unknown")

    assert response.status_code == 404
    assert "Unknown band" in response.json()["detail"]
