"""Tests to check behavior of FastAPI."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_plain_mount():
    """Tests how a nested app mounted on a base app works."""

    base_app = FastAPI()
    sub_app = FastAPI()

    base_app.mount("/mounted", sub_app)

    @base_app.get("/status1")
    def base_status():
        return {}

    @sub_app.get("/status2")
    def sub_status():
        return {}

    client = TestClient(base_app)

    assert client.get("/status1").status_code == 200
    assert client.get("/mounted/status2").status_code == 200
    assert client.get("/status2").status_code == 404

    client = TestClient(base_app, root_path="/proxy")

    assert client.get("/status1").status_code == 200
    assert client.get("/mounted/status2").status_code == 404
    assert client.get("/status2").status_code == 404
    assert client.get("/proxy/status1").status_code == 200
    assert client.get("/proxy/mounted/status2").status_code == 200
    assert client.get("/proxy/status2").status_code == 404


def test_root_path_and_plain_mount():
    """Tests how a nested app mounted on a base app with `root_path` works."""

    base_app = FastAPI(root_path="/proxy")
    sub_app = FastAPI()

    base_app.mount("/mounted", sub_app)

    @base_app.get("/status1")
    def base_status():
        return {}

    @sub_app.get("/status2")
    def sub_status():
        return {}

    client = TestClient(base_app)

    assert client.get("/proxy/status1").status_code == 200
    assert client.get("/status1").status_code == 200
    assert client.get("/proxy/mounted/status2").status_code == 200
    assert client.get("/mounted/status2").status_code == 404
    assert client.get("/status2").status_code == 404

    client = TestClient(base_app, root_path="/proxy")

    assert client.get("/proxy/status1").status_code == 200
    assert client.get("/status1").status_code == 200
    assert client.get("/proxy/mounted/status2").status_code == 200
    assert client.get("/mounted/status2").status_code == 404
    assert client.get("/status2").status_code == 404


def test_mounted_app_with_root_path():
    """Tests how a nested app mounted with `root_path` works."""

    base_app = FastAPI()
    sub_app = FastAPI(root_path="/subproxy")

    base_app.mount("/mounted", sub_app)

    @base_app.get("/status1")
    def base_status():
        return {}

    @sub_app.get("/status2")
    def sub_status():
        return {}

    client = TestClient(base_app)

    assert client.get("/subproxy/status1").status_code == 404
    assert client.get("/status1").status_code == 200
    assert client.get("/mounted/subproxy/status2").status_code == 404
    assert client.get("/subproxy/status2").status_code == 404
    assert client.get("/subproxy/mounted/status2").status_code == 404

    client = TestClient(base_app, root_path="/subproxy")

    assert client.get("/subproxy/status1").status_code == 200
    assert client.get("/status1").status_code == 200
    assert client.get("/mounted/subproxy/status2").status_code == 404
    assert client.get("/subproxy/status2").status_code == 404
    assert client.get("/subproxy/mounted/status2").status_code == 404
