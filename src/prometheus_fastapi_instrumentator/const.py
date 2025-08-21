from typing import Sequence, Union
import json
import os

DEFAULT_LATENCY_HIGHR_BUCKETS = Sequence[Union[float, str]] = (
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    4.5,
    5,
    7.5,
    10,
    30,
    60,
)
DEFAULT_LATENCY_LOWR_BUCKETS: Sequence[Union[float, str]] = (0.1, 0.5, 1)


_higher_buckets_env_var = os.getenv("FASTAPI_LATENCY_HIGHR_BUCKETS")
if _higher_buckets_env_var:
    try:
        DEFAULT_LATENCY_HIGHR_BUCKETS = tuple(json.loads(_higher_buckets_env_var))
    except json.JSONDecodeError:
        raise ValueError(
            "Invalid format for FASTAPI_LATENCY_HIGHR_BUCKETS. "
            "It should be a JSON array of numbers."
        )

_lower_buckets_env_var = os.getenv("FASTAPI_LATENCY_LOWR_BUCKETS")
if _lower_buckets_env_var:
    try:
        DEFAULT_LATENCY_LOWR_BUCKETS = tuple(json.loads(_lower_buckets_env_var))
    except json.JSONDecodeError:
        raise ValueError(
            "Invalid format for FASTAPI_LATENCY_LOWR_BUCKETS. "
            "It should be a JSON array of numbers."
        )
