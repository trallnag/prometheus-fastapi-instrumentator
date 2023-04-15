# Example `metrics-diff-port-uvicorn`

Minimal example that shows usage of Prometheus client library and Prometheus
FastAPI Instrumentator with FastAPI and Uvicorn where the `/metrics` endpoint is
exposed on another port and not on the FastAPI app itself.

Note that this does not work with multiproc mode.

To run the example, you must have run `poetry install` and `poetry shell` in the
root of this repository. The following commands are executed relative to this
directory.

Start app with Uvicorn:

```python
uvicorn main:app
```

This will start two servers:

- FastAPI app listening on port `8000`.
- Prometheus `/metrics` endpoint on port `9000`.

Interact with the app:

```shell
curl localhost:8000/ping
curl localhost:9000/metrics
```
