
"""HTTP contract tests against the independent test dataset."""

import pytest
from fastapi.testclient import TestClient

from app import main as main_module


@pytest.fixture
def client(monkeypatch, catalogue):
    # Temporarily use the synthetic catalogue for each test.
    monkeypatch.setattr(
        main_module,
        "catalogue",
        catalogue
    )

    with TestClient(main_module.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validation(client):
    response = client.get("/api/validation")

    assert response.status_code == 200

    assert response.json() == {
        "parts": 4,
        "ready": 2,
        "missing": 1,
        "not_replaceable": 1,
    }


def test_part_details(client):
    response = client.get("/api/parts/fa-9")

    assert response.status_code == 200

    assert response.json() == {
        "part_number": "FA-9",
        "description": "Latest fastener",
        "revision": "B",
        "status": "ready",
        "total_quantity": 10,
        "parents": ["AS-1", "AS-40000"],
        "children": [],
    }


def test_missing_master_part(client):
    response = client.get("/api/parts/EL-5")

    assert response.status_code == 200
    assert response.json()["status"] == "missing"
    assert response.json()["description"] is None
    assert response.json()["revision"] is None


def test_paths(client):
    response = client.get("/api/parts/FA-9/paths")

    assert response.status_code == 200

    assert response.json() == {
        "part_number": "FA-9",
        "paths": [
            ["AS-40000", "AS-1", "FA-9"],
            ["AS-40000", "FA-9"],
        ],
    }


def test_serial(client):
    response = client.get("/api/serial/1000")

    assert response.status_code == 200

    assert response.json() == {
        "serial": 1000,
        "applicable_parts": 2,
    }


@pytest.mark.parametrize(
    "invalid",
    ["abc", "12.5", "-10", "+10", "1e3"]
)
def test_bad_serial_returns_4xx(client, invalid):
    response = client.get(f"/api/serial/{invalid}")

    assert 400 <= response.status_code < 500


@pytest.mark.parametrize(
    "url",
    [
        "/api/parts/OUT-1",
        "/api/parts/UNKNOWN-999",
        "/api/parts/OUT-1/paths",
    ]
)
def test_missing_part_returns_404(client, url):
    assert client.get(url).status_code == 404


def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Arcadia" in response.text
