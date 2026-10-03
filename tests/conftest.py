"""Shared pytest fixtures.

Every test runs against a **throw-away database** in a temp directory so the
suite never touches the developer's real corpus, and so tests are
order-independent.
"""

from __future__ import annotations

import os
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """Flask app bound to an isolated SQLite file."""
    db_path = str(tmp_path_factory.mktemp("nexa") / "test.db")
    os.environ["NEXASEARCH_DB"] = db_path
    from app import create_app
    application = create_app(db_path=db_path, seed=True)
    application.config.update(TESTING=True)
    yield application
    os.environ.pop("NEXASEARCH_DB", None)


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def service(app):
    return app.extensions["nexasearch"]


@pytest.fixture(scope="session")
def db(service):
    return service.db


@pytest.fixture(scope="session")
def index(service):
    return service.index


@pytest.fixture(scope="session")
def graph(service):
    return service.graph


@pytest.fixture
def admin_client(client):
    """Client with an authenticated admin session."""
    client.post("/admin/login", data={"username": "admin", "password": "nexasearch123"})
    yield client
    client.get("/admin/logout")
