import os
import shutil

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


def is_prometheus_multiproc_valid() -> bool:
    """Checks if PROMETHEUS_MULTIPROC_DIR is set and a directory."""

    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        pmd = os.environ["PROMETHEUS_MULTIPROC_DIR"]
        if os.path.isdir(pmd):
            return True
    else:
        return False


def delete_dir_content(dirpath):
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)
