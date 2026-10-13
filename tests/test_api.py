
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation():
    response = client.get("/api/validation")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "parts": 875,
        "ready": 483,
        "missing": 25,
        "not_replaceable": 367
    }


def test_part_details():
    response = client.get("/api/parts/AS-40003")

    assert response.status_code == 200

    data = response.json()

    assert data["part_number"] == "AS-40003"
    assert data["status"] == "not_replaceable"
    assert data["total_quantity"] == 1
    assert data["parents"] == ["AS-40002"]


def test_case_insensitive_lookup():
    response = client.get("/api/parts/fa-30019")

    assert response.status_code == 200

    data = response.json()

    assert data["part_number"] == "FA-30019"
    assert data["total_quantity"] == 178


def test_unknown_part():
    response = client.get("/api/parts/UNKNOWN-999")

    assert response.status_code == 404


def test_unknown_part_paths():
    response = client.get(
        "/api/parts/UNKNOWN-999/paths"
    )

    assert response.status_code == 404


def test_root_quantity():
    response = client.get("/api/parts/AS-40000")

    assert response.status_code == 200
    assert response.json()["total_quantity"] == 1


def test_paths():
    response = client.get("/api/parts/FA-30012/paths")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert len(paths) == 17
    assert paths == sorted(paths)

    for path in paths:
        assert path[0] == "AS-40000"
        assert path[-1] == "FA-30012"


def test_serial_compatibility():
    response = client.get("/api/serial/2500")

    assert response.status_code == 200

    assert response.json() == {
        "serial": 2500,
        "applicable_parts": 448
    }


@pytest.mark.parametrize(
    "invalid_serial",
    ["abc", "12.5", "-10", "+10", "1e3"]
)
def test_invalid_serial(invalid_serial):
    response = client.get(
        f"/api/serial/{invalid_serial}"
    )

    assert 400 <= response.status_code < 500


def test_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert "Arcadia" in response.text
