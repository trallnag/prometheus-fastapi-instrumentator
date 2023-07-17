# Example `default-metrics-diff-labels`

Example that shows usage of PFI with a custom instrumentation function that
mimics the default metrics but with custom label names.

To run the example, you must have run `poetry install` and `poetry shell` in the
root of this repository. The following commands are executed relative to this
directory.

Start app with Uvicorn:

```python
uvicorn main:app
```

Interact with the app:

```shell
curl localhost:8000/ping
curl localhost:8000/metrics
```
