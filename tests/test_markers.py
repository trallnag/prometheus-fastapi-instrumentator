"""
Dummy tests that ensure that Pytest does not return an error code if no tests
are run. This would lead to failure of CI/CD pipelines, for example GitHub Actions.
"""

import pytest


@pytest.mark.slow
def test_slow():
    pass


def test_not_slow():
    pass
