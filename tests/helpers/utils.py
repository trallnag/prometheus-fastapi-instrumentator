from prometheus_client import REGISTRY


def reset_collectors() -> None:
    """Resets collectors in the default Prometheus registry.

    Modifies the `REGISTRY` registry. Supposed to be called at the beginning
    of individual test functions. Else registry is reused across test functions
    and so we can run into issues like duplicate metrics or unexpected values
    for metrics.
    """

    # Unregister all collectors.
    collectors = list(REGISTRY._collector_to_names.keys())
    print(f"before unregister collectors={collectors}")
    for collector in collectors:
        REGISTRY.unregister(collector)

    # Import default collectors.
    from prometheus_client import gc_collector, platform_collector, process_collector

    # Re-register default collectors.
    process_collector.ProcessCollector()
    platform_collector.PlatformCollector()
    gc_collector.GCCollector()

    print(f"after re-register collectors={list(REGISTRY._collector_to_names.keys())}")
