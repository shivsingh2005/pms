from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app

ALLOWED_SMOKE_STATUSES = {200, 201, 204, 400, 401, 403, 404, 405, 409, 422, 429}


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _iter_routes() -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            routes.append((method, route.path))
    return routes


def _path_value(param_name: str) -> str:
    # Keep values deterministic so failures are reproducible.
    if "id" in param_name.lower():
        return "00000000-0000-0000-0000-000000000001"
    return "sample"


def _build_path(path: str) -> str:
    built = path
    while "{" in built and "}" in built:
        start = built.index("{")
        end = built.index("}", start)
        name = built[start + 1 : end]
        built = f"{built[:start]}{_path_value(name)}{built[end + 1:]}"
    return built


def _build_query(path: str) -> dict[str, str | list[str]]:
    if path.endswith("/calendar/availability"):
        return {
            "participants_emails": ["employee@example.com", "manager@example.com"],
            "start_time": "2026-03-15T10:00:00Z",
            "end_time": "2026-03-15T11:00:00Z",
            "slot_minutes": "30",
        }
    return {}


@pytest.mark.parametrize("method,path", _iter_routes())
def test_endpoint_smoke_no_5xx(client: TestClient, method: str, path: str):
    request_path = _build_path(path)
    params = _build_query(path)
    kwargs: dict = {"params": params}

    if method in {"POST", "PUT", "PATCH"}:
        kwargs["json"] = {}

    response = client.request(method, request_path, **kwargs)

    assert response.status_code in ALLOWED_SMOKE_STATUSES, (
        f"Unexpected status {response.status_code} for {method} {path}. "
        f"Response body: {response.text}"
    )


def test_endpoint_surface_is_non_trivial():
    # Prevent accidental route drops from going unnoticed.
    assert len(_iter_routes()) >= 40
