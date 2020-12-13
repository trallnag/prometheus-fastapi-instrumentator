# Copyright © 2020 Tim Schwenke <tim.and.trallnag+code@gmail.com>
# Licensed under Apache License 2.0 <http://www.apache.org/licenses/LICENSE-2.0>

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
