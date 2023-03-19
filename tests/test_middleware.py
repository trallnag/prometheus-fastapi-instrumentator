from fastapi import FastAPI, responses, status
from fastapi.testclient import TestClient

from prometheus_fastapi_instrumentator import Instrumentator, metrics


def test_info_body_empty():
    """
    Tests that `info.response.body` is empty if actual response is also empty.
    """

    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def read_root():
        return responses.Response(status_code=status.HTTP_200_OK)

    instrumentation_executed = False

    def instrumentation(info: metrics.Info) -> None:
        nonlocal instrumentation_executed
        instrumentation_executed = True
        assert len(info.response.body) == 0

    Instrumentator().instrument(app).add(instrumentation)

    client.get("/")
    assert instrumentation_executed


def test_info_body_stream_small():
    """
    Tests that `info.response.body` is correct if small response is streamed.
    """

    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def read_root():
        return responses.StreamingResponse((str(num) + "xxx" for num in range(5)))

    instrumentation_executed = False

    def instrumentation(info: metrics.Info) -> None:
        nonlocal instrumentation_executed
        instrumentation_executed = True
        assert len(info.response.body) == 20
        assert info.response.body.decode() == "0xxx1xxx2xxx3xxx4xxx"

    Instrumentator().instrument(app).add(instrumentation)

    response = client.get("/")
    assert instrumentation_executed
    assert len(response.content) == 20
    assert response.content.decode() == "0xxx1xxx2xxx3xxx4xxx"


def test_info_body_stream_large():
    """
    Tests that `info.response.body` is correct if large response is streamed.
    """

    app = FastAPI()
    client = TestClient(app)

    @app.get("/")
    def read_root():
        return responses.StreamingResponse(
            (str(num) + "x" * 10000000 for num in range(5))
        )

    instrumentation_executed = False

    def instrumentation(info: metrics.Info) -> None:
        nonlocal instrumentation_executed
        instrumentation_executed = True
        assert len(info.response.body) >= 50000000

    Instrumentator().instrument(app).add(instrumentation)

    response = client.get("/")
    assert instrumentation_executed
    assert len(response.content) >= 50000000


def test_info_body_bulk_small():
    """
    Tests that `info.response.body` is correct if small response is returned.
    """

    app = FastAPI()
    client = TestClient(app)

    @app.get("/", response_class=responses.PlainTextResponse)
    def read_root():
        return "123456789"

    instrumentation_executed = False

    def instrumentation(info: metrics.Info) -> None:
        print(info.response.body)
        nonlocal instrumentation_executed
        instrumentation_executed = True
        assert len(info.response.body) == 9
        assert info.response.body == b"123456789"

    Instrumentator().instrument(app).add(instrumentation)

    response = client.get("/")
    assert instrumentation_executed
    assert len(response.content) == 9
    assert response.content == b"123456789"


def test_info_body_bulk_large():
    """
    Tests that `info.response.body` is correct if large response is returned.
    """

    app = FastAPI()
    client = TestClient(app)

    @app.get("/", response_class=responses.PlainTextResponse)
    def read_root():
        return "x" * 50_000_000

    instrumentation_executed = False

    def instrumentation(info: metrics.Info) -> None:
        print(info.response.body)
        nonlocal instrumentation_executed
        instrumentation_executed = True
        assert len(info.response.body) == 50_000_000

    Instrumentator().instrument(app).add(instrumentation)

    response = client.get("/")
    assert instrumentation_executed
    assert len(response.content) == 50_000_000
